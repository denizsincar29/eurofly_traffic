package eurofly

import "strings"

// Countries maps country IDs to country names.
var Countries = map[int]string{
	1:   "Algeria",
	5:   "Burkina Faso",
	15:  "Egypt",
	19:  "Ethiopia",
	22:  "Ghana",
	23:  "Guinea",
	26:  "Kenya",
	29:  "Libya",
	31:  "Malawi",
	36:  "Morocco",
	45:  "Senegal",
	49:  "South Africa",
	54:  "Tunisia",
	59:  "Afghanistan",
	60:  "Armenia",
	61:  "Azerbaijan",
	63:  "Bangladesh",
	67:  "Cambodia",
	68:  "Georgia",
	70:  "China",
	71:  "India",
	72:  "Indonesia",
	73:  "Iran",
	74:  "Iraq",
	75:  "Israel",
	76:  "Japan",
	77:  "Jordan",
	78:  "Kazakhstan",
	79:  "North Korea",
	80:  "South Korea",
	81:  "Kuwait",
	84:  "Lebanon",
	86:  "Malaisia",
	88:  "Mongolia",
	89:  "Miammar",
	90:  "Nepal",
	92:  "Pakistan",
	93:  "Palestinian Territories",
	94:  "Philippines",
	96:  "Saudi Arabia",
	97:  "Singapore",
	98:  "Sri Lanka",
	99:  "Syria",
	100: "Taiwan",
	102: "Thailand",
	103: "Turkey",
	106: "Uzbekistan",
	107: "Vietnam",
	108: "Yemen",
	109: "Aland Islands",
	110: "Albania",
	111: "Andorra",
	112: "Austria",
	113: "Belarus",
	114: "Belgium",
	115: "Bosnia and Herzegovina",
	116: "Bulgaria",
	117: "Croatia",
	118: "Cyprus",
	119: "Czech Republic",
	120: "Denmark",
	121: "Estonia",
	123: "Finland",
	124: "France",
	125: "Germany",
	126: "Gibraltar",
	127: "Greece",
	130: "Hungary",
	131: "Iceland",
	132: "Ireland",
	134: "Italy",
	137: "Latvia",
	139: "Lithuania",
	140: "Luxembourg",
	141: "Malta",
	145: "Netherlands",
	146: "North Macedonia",
	147: "Norway",
	148: "Poland",
	149: "Portugal",
	150: "Romania",
	151: "Russia",
	153: "Serbia",
	154: "Slovakia",
	155: "Slovenia",
	156: "Spain",
	158: "Sweden",
	159: "Switzerland",
	160: "Ukraine",
	164: "Aruba",
	167: "Belize",
	172: "Costa Rica",
	173: "Cuba",
	176: "Dominican Republic",
	177: "Salvador",
	179: "Grenada",
	181: "Guatemala",
	183: "Honduras",
	184: "Jamaica",
}

// CountryNameToID provides reverse lookup from country name to ID (case-insensitive).
var CountryNameToID map[string]int

func init() {
	CountryNameToID = make(map[string]int, len(Countries))
	for id, name := range Countries {
		CountryNameToID[strings.ToLower(name)] = id
	}
}

// Ranks maps rank levels to rank names.
var Ranks = map[int]string{
	1: "intraining",
	2: "novices",
	3: "assistants",
	4: "copilot",
	5: "first pilot",
	6: "captain",
	7: "teacher pilot",
}

// FlightTypes maps flight type codes to full names.
var FlightTypes = map[string]string{
	"FRE": "Free flight",
	"COF": "Company flight",
	"CHF": "Charter flight",
	"BCF": "Business cargo flight",
	"BTF": "Business transport flight",
	"MAF": "MAF flight",
}

// FlightTypeToCode provides reverse lookup from flight type name to code (case-insensitive).
var FlightTypeToCode map[string]string

func init() {
	FlightTypeToCode = make(map[string]string, len(FlightTypes))
	for code, name := range FlightTypes {
		FlightTypeToCode[strings.ToLower(name)] = code
	}
}
