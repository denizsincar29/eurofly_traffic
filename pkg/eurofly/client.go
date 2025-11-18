package eurofly

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"regexp"
	"strconv"
	"strings"

	"github.com/PuerkitoBio/goquery"
)

const (
	// BaseURL is the base URL for Eurofly API.
	BaseURL = "https://eurofly.stefankiss.sk/ef3"

	// DefaultCacheFile is the default cache file name.
	DefaultCacheFile = ".cache.json"
)

// Client is the main client for interacting with Eurofly.
type Client struct {
	httpClient *http.Client
	cacheFile  string
	cache      map[string]interface{}
}

// NewClient creates a new Eurofly client.
func NewClient(cacheFile string) *Client {
	if cacheFile == "" {
		cacheFile = DefaultCacheFile
	}
	client := &Client{
		httpClient: &http.Client{},
		cacheFile:  cacheFile,
		cache:      make(map[string]interface{}),
	}
	client.loadCache()
	return client
}

// loadCache loads pilot profiles from cache file.
func (c *Client) loadCache() {
	if _, err := os.Stat(c.cacheFile); os.IsNotExist(err) {
		return
	}
	data, err := os.ReadFile(c.cacheFile)
	if err != nil {
		return
	}
	_ = json.Unmarshal(data, &c.cache)
}

// saveCache saves pilot profiles to cache file.
func (c *Client) saveCache() {
	data, err := json.MarshalIndent(c.cache, "", "  ")
	if err != nil {
		return
	}
	_ = os.WriteFile(c.cacheFile, data, 0644)
}

// FetchTrafficHTML fetches the current traffic HTML from Eurofly.
func (c *Client) FetchTrafficHTML(ctx context.Context) (string, error) {
	data := url.Values{}
	data.Set("type", "xhr")
	data.Set("offset", "-180")
	data.Set("method", "current_flights3")
	data.Set("let", `""`)

	req, err := http.NewRequestWithContext(ctx, "POST", BaseURL+"/[object%20Object]", strings.NewReader(data.Encode()))
	if err != nil {
		return "", err
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0")
	req.Header.Set("X-Requested-With", "XMLHttpRequest")
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	return string(body), nil
}

// ParseTraffic parses traffic HTML into a Traffic object.
func (c *Client) ParseTraffic(html string) (*Traffic, error) {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		return nil, err
	}

	traffic := NewTraffic()

	parseSection := func(headerText string) []Pilot {
		var pilots []Pilot

		// Find the section header
		var foundHeader *goquery.Selection
		doc.Find("center").Each(func(i int, s *goquery.Selection) {
			text := s.Text()
			if strings.Contains(text, headerText) {
				foundHeader = s
			}
		})

		if foundHeader == nil {
			return pilots
		}

		// Find all pilot entries after the header until next section
		stopAtNextSection := false
		foundHeader.NextAll().EachWithBreak(func(i int, center *goquery.Selection) bool {
			if center.Is("center") == false {
				return true // continue
			}

			// Check if this is another section header - if so, stop parsing
			centerText := strings.TrimSpace(center.Text())
			if centerText == "On earth" || centerText == "In air" {
				stopAtNextSection = true
				return false // break
			}
			
			if stopAtNextSection {
				return false // break
			}

			h3 := center.Find("h3")
			if h3.Length() == 0 {
				return true // continue
			}

			a := h3.Find("a")
			if a.Length() == 0 {
				return true // continue
			}

			href, exists := a.Attr("href")
			if !exists || !strings.Contains(href, "/ef3/pilot") {
				return true // continue
			}

			text := strings.TrimSpace(a.Text())

			// Extract pilot ID
			var pilotID *int
			re := regexp.MustCompile(`pid=(\d+)`)
			if matches := re.FindStringSubmatch(href); len(matches) > 1 {
				if id, err := strconv.Atoi(matches[1]); err == nil {
					pilotID = &id
				}
			}

			// Parse name, callsign, and flight type
			name, callsign, flightType := "", "", ""
			if idx := strings.LastIndex(text, " - "); idx != -1 {
				nameCallsign := text[:idx]
				flightType = text[idx+3:]
				if idx2 := strings.LastIndex(nameCallsign, " "); idx2 != -1 {
					name = nameCallsign[:idx2]
					callsign = nameCallsign[idx2+1:]
				} else {
					name = nameCallsign
				}
			} else {
				if idx := strings.LastIndex(text, " "); idx != -1 {
					name = text[:idx]
					callsign = text[idx+1:]
				} else {
					name = text
				}
			}

			// Collect flight information lines
			// The HTML structure is: <center>pilot info</center><br>line1<br>line2<br>...<br><br><center>next pilot</center>
			// The HTML parser converts <br> to text nodes with data "br", and actual text is in element nodes
			var flightLines []string
			node := center.Get(0)
			
			// Start from the node after </center>
			for sibling := node.NextSibling; sibling != nil; sibling = sibling.NextSibling {
				// Stop when we hit another center tag (text node with data "center")
				if sibling.Type == 3 && sibling.Data == "center" {
					break
				}
				
				// Text content is in Type 1 nodes (element nodes)
				if sibling.Type == 1 {
					line := strings.TrimSpace(sibling.Data)
					// Skip empty lines
					if line != "" {
						flightLines = append(flightLines, line)
					}
				}
			}

			// Parse flight information
			flight := Flight{}
			var unrecognizedLines []string

			for _, line := range flightLines {
				recognized := false

				if strings.Contains(line, "with") && strings.Contains(line, "passengers") {
					parts := strings.Split(line, "with")
					if len(parts) == 2 {
						aircraft := strings.TrimSpace(parts[0])
						flight.Aircraft = &aircraft
						paxPart := strings.Split(parts[1], "passengers")
						if len(paxPart) > 0 {
							if pax, err := strconv.Atoi(strings.TrimSpace(paxPart[0])); err == nil {
								flight.Passengers = pax
							}
						}
					}
					recognized = true
				} else if line == "Crashed" {
					status := "Crashed"
					flight.Status = &status
					recognized = true
				} else if strings.Contains(line, "Standing at") {
					status := "Standing"
					flight.Status = &status
					parts := strings.Split(line, "Standing at")
					if len(parts) > 1 {
						loc := strings.TrimSpace(parts[1])
						flight.LocationFrom = &loc
					}
					recognized = true
				} else if strings.Contains(line, "Rolling at") {
					status := "Rolling"
					flight.Status = &status
					parts := strings.Split(line, "Rolling at")
					if len(parts) > 1 {
						loc := strings.TrimSpace(parts[1])
						flight.LocationFrom = &loc
					}
					recognized = true
				} else if strings.Contains(line, "Taking off at") {
					status := "Taking off"
					flight.Status = &status
					parts := strings.Split(line, "Taking off at")
					if len(parts) > 1 {
						loc := strings.TrimSpace(parts[1])
						flight.LocationFrom = &loc
					}
					recognized = true
				} else if strings.Contains(line, "Landing at") {
					status := "Landing"
					flight.Status = &status
					parts := strings.Split(line, "Landing at")
					if len(parts) > 1 {
						loc := strings.TrimSpace(parts[1])
						flight.LocationTo = &loc
					}
					recognized = true
				} else if strings.Contains(line, "Took of from") {
					status := "In air"
					flight.Status = &status
					parts := strings.Split(line, "Took of from:")
					if len(parts) > 1 {
						loc := strings.TrimSpace(parts[1])
						flight.LocationFrom = &loc
					}
					recognized = true
				} else if strings.HasPrefix(line, "Course:") {
					loc := strings.TrimSpace(strings.TrimPrefix(line, "Course:"))
					flight.LocationTo = &loc
					recognized = true
				} else if strings.HasPrefix(line, "Last known position:") {
					pos := strings.TrimSpace(strings.TrimPrefix(line, "Last known position:"))
					flight.LastPosition = &pos
					recognized = true
				} else if strings.HasPrefix(line, "Flightplan:") {
					plan := strings.TrimSpace(strings.TrimPrefix(line, "Flightplan:"))
					locations := strings.Split(plan, " - ")
					if len(locations) > 0 {
						from := strings.TrimSpace(locations[0])
						flight.LocationFrom = &from
						if len(locations) > 1 {
							to := strings.TrimSpace(locations[len(locations)-1])
							flight.LocationTo = &to
						}
					}
					recognized = true
				} else if strings.HasPrefix(line, "No flightplan") {
					recognized = true
				}

				if !recognized && line != "" {
					unrecognizedLines = append(unrecognizedLines, line)
				}
			}

			// Last unrecognized line is the description
			if len(unrecognizedLines) > 0 {
				desc := unrecognizedLines[len(unrecognizedLines)-1]
				flight.Description = &desc
			}

			// Debug log if status is nil
			if flight.Status == nil {
				log.Printf("⚠️  Status=nil for %s (%s) | Flight lines: %v\n", name, callsign, flightLines)
			}

			pilot := Pilot{
				Name:       name,
				Callsign:   callsign,
				FlightType: flightType,
				Flight:     flight,
				PilotID:    pilotID,
			}
			pilot.SetClient(c)
			pilots = append(pilots, pilot)
			return true // continue to next pilot
		})

		return pilots
	}

	traffic.PilotsOnGround = parseSection("On earth")
	traffic.PilotsInAir = parseSection("In air")

	return traffic, nil
}

// GetTraffic fetches and parses current traffic.
func (c *Client) GetTraffic(ctx context.Context) (*Traffic, error) {
	html, err := c.FetchTrafficHTML(ctx)
	if err != nil {
		return nil, err
	}
	return c.ParseTraffic(html)
}

// FetchPilotProfileHTML fetches the HTML of a pilot's profile page.
func (c *Client) FetchPilotProfileHTML(ctx context.Context, pilotID int) (string, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", fmt.Sprintf("%s/pilot?pid=%d", BaseURL, pilotID), nil)
	if err != nil {
		return "", err
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}

	return string(body), nil
}

// ParsePilotProfile parses a pilot's profile HTML.
func (c *Client) ParsePilotProfile(html string, pilotID int) (*PilotProfile, error) {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		return nil, err
	}

	profile := &PilotProfile{
		PilotID: pilotID,
	}

	contentDiv := doc.Find("div.content")
	if contentDiv.Length() == 0 {
		return nil, fmt.Errorf("could not find content div in pilot profile page")
	}

	// Extract bio from h2 tags
	contentDiv.Find("h2").Each(func(i int, h2 *goquery.Selection) {
		text := h2.Text()
		if strings.Contains(text, "About the pilot") {
			lines := strings.Split(text, "\n")
			var bioLines []string
			for _, line := range lines {
				line = strings.TrimSpace(line)
				if line != "" && line != "About the pilot" {
					bioLines = append(bioLines, line)
				}
			}
			if len(bioLines) > 0 {
				bio := strings.Join(bioLines, "\n")
				profile.Bio = &bio
			}
		}
	})

	// Get all text content
	text := contentDiv.Text()
	lines := strings.Split(text, "\n")
	var cleanLines []string
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line != "" {
			cleanLines = append(cleanLines, line)
		}
	}

	// Parse first line for pilot name and rank
	if len(cleanLines) > 0 {
		firstLine := cleanLines[0]
		re := regexp.MustCompile(`Pilot (.+?) - (.+?) - (\d+)`)
		if matches := re.FindStringSubmatch(firstLine); len(matches) > 3 {
			profile.Name = matches[1]
			rank := matches[2]
			profile.Rank = &rank
			if rankNum, err := strconv.Atoi(matches[3]); err == nil {
				profile.RankNumber = &rankNum
			}
		} else {
			re = regexp.MustCompile(`Pilot (.+)`)
			if matches := re.FindStringSubmatch(firstLine); len(matches) > 1 {
				profile.Name = matches[1]
			}
		}
	}

	// Parse other fields
	for i := 1; i < len(cleanLines); i++ {
		line := cleanLines[i]

		if strings.HasPrefix(line, "Sex:") && i+1 < len(cleanLines) {
			sex := cleanLines[i+1]
			profile.Sex = &sex
			i++
		} else if strings.HasPrefix(line, "Country:") {
			country := strings.TrimSpace(strings.TrimPrefix(line, "Country:"))
			profile.Country = &country
		} else if strings.HasPrefix(line, "Language:") {
			language := strings.TrimSpace(strings.TrimPrefix(line, "Language:"))
			profile.Language = &language
		} else if strings.Contains(line, "years old") {
			re := regexp.MustCompile(`(\d+) years old`)
			if matches := re.FindStringSubmatch(line); len(matches) > 1 {
				if age, err := strconv.Atoi(matches[1]); err == nil {
					profile.Age = &age
				}
			}
		} else if strings.HasPrefix(line, "Rank") && !strings.HasPrefix(line, "Rank:") {
			re := regexp.MustCompile(`Rank (\d+)`)
			if matches := re.FindStringSubmatch(line); len(matches) > 1 {
				if rank, err := strconv.Atoi(matches[1]); err == nil {
					profile.OverallRank = &rank
				}
			}
		} else if strings.HasPrefix(line, "Registered:") {
			registered := strings.TrimSpace(strings.TrimPrefix(line, "Registered:"))
			profile.Registered = &registered
		} else if strings.HasPrefix(line, "Last login:") {
			lastLogin := strings.TrimSpace(strings.TrimPrefix(line, "Last login:"))
			profile.LastLogin = &lastLogin
		} else if strings.HasPrefix(line, "Last performed flight:") {
			lastFlight := strings.TrimSpace(strings.TrimPrefix(line, "Last performed flight:"))
			profile.LastFlight = &lastFlight
		} else if strings.HasPrefix(line, "Points:") {
			re := regexp.MustCompile(`Points: (\d+)`)
			if matches := re.FindStringSubmatch(line); len(matches) > 1 {
				if points, err := strconv.Atoi(matches[1]); err == nil {
					profile.Points = &points
				}
			}
		} else if strings.HasPrefix(line, "Earnings:") {
			re := regexp.MustCompile(`Earnings: (\d+)`)
			if matches := re.FindStringSubmatch(line); len(matches) > 1 {
				if earnings, err := strconv.Atoi(matches[1]); err == nil {
					profile.Earnings = &earnings
				}
			}
		} else if strings.HasPrefix(line, "Flights overall:") {
			re := regexp.MustCompile(`Flights overall: (\d+)`)
			if matches := re.FindStringSubmatch(line); len(matches) > 1 {
				if flights, err := strconv.Atoi(matches[1]); err == nil {
					profile.FlightsOverall = &flights
				}
			}
		} else if strings.HasPrefix(line, "Total distance travelled:") {
			re := regexp.MustCompile(`Total distance travelled: ([\d,]+) Km`)
			if matches := re.FindStringSubmatch(line); len(matches) > 1 {
				distStr := strings.ReplaceAll(matches[1], ",", "")
				if dist, err := strconv.Atoi(distStr); err == nil {
					profile.TotalDistanceKm = &dist
				}
			}
		} else if strings.HasPrefix(line, "Total time spent flying:") {
			re := regexp.MustCompile(`Total time spent flying: (.+)`)
			if matches := re.FindStringSubmatch(line); len(matches) > 1 {
				time := matches[1]
				profile.TotalFlightTime = &time
			}
		}
	}

	return profile, nil
}

// GetPilotProfile fetches and parses a pilot's profile.
func (c *Client) GetPilotProfile(pilotID int, useCache bool) (*PilotProfile, error) {
	return c.GetPilotProfileWithContext(context.Background(), pilotID, useCache)
}

// GetPilotProfileWithContext fetches and parses a pilot's profile with context.
func (c *Client) GetPilotProfileWithContext(ctx context.Context, pilotID int, useCache bool) (*PilotProfile, error) {
	cacheKey := strconv.Itoa(pilotID)

	// Try cache first
	if useCache {
		if cached, ok := c.cache[cacheKey]; ok {
			// Convert cached data back to PilotProfile
			data, err := json.Marshal(cached)
			if err == nil {
				var profile PilotProfile
				if err := json.Unmarshal(data, &profile); err == nil {
					return &profile, nil
				}
			}
		}
	}

	// Fetch from server
	html, err := c.FetchPilotProfileHTML(ctx, pilotID)
	if err != nil {
		return nil, err
	}

	profile, err := c.ParsePilotProfile(html, pilotID)
	if err != nil {
		return nil, err
	}

	// Save to cache
	if useCache {
		c.cache[cacheKey] = profile
		c.saveCache()
	}

	return profile, nil
}

// SearchPilots searches for pilots by name.
func (c *Client) SearchPilots(ctx context.Context, query string) ([]struct {
	ID   int
	Name string
}, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", BaseURL+"/pilots", nil)
	if err != nil {
		return nil, err
	}

	q := req.URL.Query()
	q.Add("name", query)
	req.URL.RawQuery = q.Encode()

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, err
	}

	var results []struct {
		ID   int
		Name string
	}

	doc.Find("a[href*='/ef3/pilot?pid=']").Each(func(i int, s *goquery.Selection) {
		href, exists := s.Attr("href")
		if !exists {
			return
		}

		text := strings.TrimSpace(s.Text())
		re := regexp.MustCompile(`pid=(\d+)`)
		if matches := re.FindStringSubmatch(href); len(matches) > 1 {
			if id, err := strconv.Atoi(matches[1]); err == nil {
				results = append(results, struct {
					ID   int
					Name string
				}{ID: id, Name: text})
			}
		}
	})

	return results, nil
}

// SearchPilotsByCountry searches for pilots by country ID.
func (c *Client) SearchPilotsByCountry(ctx context.Context, countryID int) ([]struct {
	ID   int
	Name string
}, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", BaseURL+"/pilots", nil)
	if err != nil {
		return nil, err
	}

	q := req.URL.Query()
	q.Add("state", strconv.Itoa(countryID))
	req.URL.RawQuery = q.Encode()

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, err
	}

	var results []struct {
		ID   int
		Name string
	}

	doc.Find("a[href*='/ef3/pilot?pid=']").Each(func(i int, s *goquery.Selection) {
		href, exists := s.Attr("href")
		if !exists {
			return
		}

		text := strings.TrimSpace(s.Text())
		re := regexp.MustCompile(`pid=(\d+)`)
		if matches := re.FindStringSubmatch(href); len(matches) > 1 {
			if id, err := strconv.Atoi(matches[1]); err == nil {
				results = append(results, struct {
					ID   int
					Name string
				}{ID: id, Name: text})
			}
		}
	})

	return results, nil
}

// SearchPilotsByRank searches for pilots by rank level.
func (c *Client) SearchPilotsByRank(ctx context.Context, rankLevel int) ([]struct {
	ID   int
	Name string
}, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", BaseURL+"/pilots", nil)
	if err != nil {
		return nil, err
	}

	q := req.URL.Query()
	q.Add("level", strconv.Itoa(rankLevel))
	req.URL.RawQuery = q.Encode()

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, err
	}

	var results []struct {
		ID   int
		Name string
	}

	doc.Find("a[href*='/ef3/pilot?pid=']").Each(func(i int, s *goquery.Selection) {
		href, exists := s.Attr("href")
		if !exists {
			return
		}

		text := strings.TrimSpace(s.Text())
		re := regexp.MustCompile(`pid=(\d+)`)
		if matches := re.FindStringSubmatch(href); len(matches) > 1 {
			if id, err := strconv.Atoi(matches[1]); err == nil {
				results = append(results, struct {
					ID   int
					Name string
				}{ID: id, Name: text})
			}
		}
	})

	return results, nil
}

// SearchPilotsAdvanced searches for pilots using multiple criteria.
func (c *Client) SearchPilotsAdvanced(ctx context.Context, name *string, countryID *int, rankLevel *int) ([]struct {
	ID   int
	Name string
}, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", BaseURL+"/pilots", nil)
	if err != nil {
		return nil, err
	}

	q := req.URL.Query()
	if name != nil {
		q.Add("name", *name)
	}
	if countryID != nil {
		q.Add("state", strconv.Itoa(*countryID))
	}
	if rankLevel != nil {
		q.Add("level", strconv.Itoa(*rankLevel))
	}
	req.URL.RawQuery = q.Encode()

	if q.Encode() == "" {
		return []struct {
			ID   int
			Name string
		}{}, nil
	}

	req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return nil, err
	}

	var results []struct {
		ID   int
		Name string
	}

	doc.Find("a[href*='/ef3/pilot?pid=']").Each(func(i int, s *goquery.Selection) {
		href, exists := s.Attr("href")
		if !exists {
			return
		}

		text := strings.TrimSpace(s.Text())
		re := regexp.MustCompile(`pid=(\d+)`)
		if matches := re.FindStringSubmatch(href); len(matches) > 1 {
			if id, err := strconv.Atoi(matches[1]); err == nil {
				results = append(results, struct {
					ID   int
					Name string
				}{ID: id, Name: text})
			}
		}
	})

	return results, nil
}
