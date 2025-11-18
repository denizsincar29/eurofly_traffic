package eurofly

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strconv"
	"strings"

	"github.com/PuerkitoBio/goquery"
)

// FetchAirplanesHTML fetches the private airplanes HTML page.
func (c *Client) FetchAirplanesHTML(ctx context.Context, sortBy *string) (string, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", BaseURL+"/private-planes", nil)
	if err != nil {
		return "", err
	}

	if sortBy != nil {
		q := req.URL.Query()
		q.Add("sort", *sortBy)
		req.URL.RawQuery = q.Encode()
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

// ParseAirplanes parses airplanes HTML into a slice of Airplane objects.
func (c *Client) ParseAirplanes(html string) ([]Airplane, error) {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		return nil, err
	}

	var airplanes []Airplane

	// Find the main table
	table := doc.Find("table").First()
	if table.Length() == 0 {
		return airplanes, nil
	}

	// Find all rows, skip header
	table.Find("tr").Each(func(i int, row *goquery.Selection) {
		if i == 0 {
			return // Skip header row
		}

		cols := row.Find("td")
		if cols.Length() < 12 {
			return
		}

		var airplane Airplane
		var err error

		airplane.Row, err = strconv.Atoi(strings.TrimSpace(cols.Eq(0).Text()))
		if err != nil {
			return
		}

		airplane.Name = strings.TrimSpace(cols.Eq(1).Text())

		airplane.Category, err = strconv.Atoi(strings.TrimSpace(cols.Eq(2).Text()))
		if err != nil {
			return
		}

		airplane.Type = strings.TrimSpace(cols.Eq(3).Text())
		airplane.PropulsionType = strings.TrimSpace(cols.Eq(4).Text())

		airplane.Engines, err = strconv.Atoi(strings.TrimSpace(cols.Eq(5).Text()))
		if err != nil {
			return
		}

		airplane.Passengers, err = strconv.Atoi(strings.TrimSpace(cols.Eq(6).Text()))
		if err != nil {
			return
		}

		airplane.SpeedKmh, err = strconv.Atoi(strings.TrimSpace(cols.Eq(7).Text()))
		if err != nil {
			return
		}

		airplane.RangeKm, err = strconv.Atoi(strings.TrimSpace(cols.Eq(8).Text()))
		if err != nil {
			return
		}

		airplane.CruisingAltitudeM, err = strconv.Atoi(strings.TrimSpace(cols.Eq(9).Text()))
		if err != nil {
			return
		}

		airplane.Price, err = strconv.Atoi(strings.TrimSpace(cols.Eq(10).Text()))
		if err != nil {
			return
		}

		airplane.QualificationPrice, err = strconv.Atoi(strings.TrimSpace(cols.Eq(11).Text()))
		if err != nil {
			return
		}

		airplanes = append(airplanes, airplane)
	})

	return airplanes, nil
}

// GetAirplanes fetches and parses all private airplanes.
func (c *Client) GetAirplanes(ctx context.Context, sortBy *string) ([]Airplane, error) {
	html, err := c.FetchAirplanesHTML(ctx, sortBy)
	if err != nil {
		return nil, err
	}
	return c.ParseAirplanes(html)
}

// FilterAirplanesByPassengers filters airplanes by passenger capacity.
func FilterAirplanesByPassengers(airplanes []Airplane, minPassengers int, maxPassengers *int) []Airplane {
	var filtered []Airplane
	for _, a := range airplanes {
		if maxPassengers == nil {
			if a.Passengers >= minPassengers {
				filtered = append(filtered, a)
			}
		} else {
			if a.Passengers >= minPassengers && a.Passengers <= *maxPassengers {
				filtered = append(filtered, a)
			}
		}
	}
	return filtered
}

// FilterAirplanesByPrice filters airplanes by maximum price.
func FilterAirplanesByPrice(airplanes []Airplane, maxPrice int) []Airplane {
	var filtered []Airplane
	for _, a := range airplanes {
		if a.Price <= maxPrice {
			filtered = append(filtered, a)
		}
	}
	return filtered
}

// FilterAirplanesByCategory filters airplanes by category.
func FilterAirplanesByCategory(airplanes []Airplane, category int) []Airplane {
	var filtered []Airplane
	for _, a := range airplanes {
		if a.Category == category {
			filtered = append(filtered, a)
		}
	}
	return filtered
}

// FetchAirportsHTML fetches the airports HTML page.
func (c *Client) FetchAirportsHTML(ctx context.Context, countryID *int, category *int) (string, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", BaseURL+"/airports", nil)
	if err != nil {
		return "", err
	}

	q := req.URL.Query()
	if countryID != nil {
		q.Add("state", strconv.Itoa(*countryID))
	}
	if category != nil {
		q.Add("cat", strconv.Itoa(*category))
	}
	req.URL.RawQuery = q.Encode()

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

// ParseAirports parses airports HTML into a slice of Airport objects.
func (c *Client) ParseAirports(html string) ([]Airport, error) {
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		return nil, err
	}

	var airports []Airport

	doc.Find("h3").Each(func(i int, h3 *goquery.Selection) {
		text := h3.Text()
		parts := strings.Split(text, " - ")
		if len(parts) < 2 {
			return
		}

		airport := Airport{
			Name: strings.TrimSpace(parts[0]),
		}

		if len(parts) > 1 {
			code := strings.TrimSpace(parts[1])
			airport.Code = &code
		}

		if len(parts) > 2 {
			airportType := strings.TrimSpace(parts[2])
			airport.Type = &airportType
		}

		// Get the parent center tag and find next siblings
		center := h3.Parent()
		var nextElements []string
		for node := center.Get(0).NextSibling; node != nil && len(nextElements) < 3; node = node.NextSibling {
			if node.Type == 3 { // Text node
				text := strings.TrimSpace(node.Data)
				if text != "" && text != "--" {
					nextElements = append(nextElements, text)
				}
			}
		}

		// Parse location line
		if len(nextElements) > 0 {
			locationText := nextElements[0]
			locationParts := strings.Split(locationText, " - ")
			for i, part := range locationParts {
				locationParts[i] = strings.TrimSpace(part)
			}
			if len(locationParts) > 0 && locationParts[0] != "" {
				country := locationParts[0]
				airport.Country = &country
			}
			if len(locationParts) > 1 && locationParts[1] != "" {
				region := locationParts[1]
				airport.Region = &region
			}
		}

		// Parse details line
		if len(nextElements) > 1 {
			detailsText := nextElements[1]

			if matches := regexp.MustCompile(`Cat:\s*(\d+)`).FindStringSubmatch(detailsText); len(matches) > 1 {
				if cat, err := strconv.Atoi(matches[1]); err == nil {
					airport.Category = &cat
				}
			}

			if matches := regexp.MustCompile(`Difficulty:\s*(\d+)`).FindStringSubmatch(detailsText); len(matches) > 1 {
				if diff, err := strconv.Atoi(matches[1]); err == nil {
					airport.Difficulty = &diff
				}
			}

			if matches := regexp.MustCompile(`Latitude:\s*([\d.-]+)`).FindStringSubmatch(detailsText); len(matches) > 1 {
				if lat, err := strconv.ParseFloat(matches[1], 64); err == nil {
					airport.Latitude = &lat
				}
			}

			if matches := regexp.MustCompile(`Longitude:\s*([\d.-]+)`).FindStringSubmatch(detailsText); len(matches) > 1 {
				if lon, err := strconv.ParseFloat(matches[1], 64); err == nil {
					airport.Longitude = &lon
				}
			}

			if matches := regexp.MustCompile(`elevation\s+(\d+)`).FindStringSubmatch(detailsText); len(matches) > 1 {
				if elev, err := strconv.Atoi(matches[1]); err == nil {
					airport.Elevation = &elev
				}
			}
		}

		// Parse runway info
		if len(nextElements) > 2 {
			runwayText := nextElements[2]

			if matches := regexp.MustCompile(`Runways:\s*(\d+)`).FindStringSubmatch(runwayText); len(matches) > 1 {
				if runways, err := strconv.Atoi(matches[1]); err == nil {
					airport.Runways = &runways
				}
			}

			if matches := regexp.MustCompile(`Aproach frequency:\s*([\d.]+)`).FindStringSubmatch(runwayText); len(matches) > 1 {
				if freq, err := strconv.ParseFloat(matches[1], 64); err == nil {
					airport.ApproachFrequency = &freq
				}
			}
		}

		airports = append(airports, airport)
	})

	return airports, nil
}

// GetAirports fetches and parses airports.
func (c *Client) GetAirports(ctx context.Context, countryID *int, category *int) ([]Airport, error) {
	html, err := c.FetchAirportsHTML(ctx, countryID, category)
	if err != nil {
		return nil, err
	}
	return c.ParseAirports(html)
}

// FilterAirportsByRunwayLength filters airports by minimum number of runways.
func FilterAirportsByRunwayLength(airports []Airport, minRunways int) []Airport {
	var filtered []Airport
	for _, a := range airports {
		if a.Runways != nil && *a.Runways >= minRunways {
			filtered = append(filtered, a)
		}
	}
	return filtered
}

// FilterAirportsByCategory filters airports by category.
func FilterAirportsByCategory(airports []Airport, category int) []Airport {
	var filtered []Airport
	for _, a := range airports {
		if a.Category != nil && *a.Category == category {
			filtered = append(filtered, a)
		}
	}
	return filtered
}

// FilterAirportsByElevation filters airports by maximum elevation.
func FilterAirportsByElevation(airports []Airport, maxElevation int) []Airport {
	var filtered []Airport
	for _, a := range airports {
		if a.Elevation != nil && *a.Elevation <= maxElevation {
			filtered = append(filtered, a)
		}
	}
	return filtered
}
