package eurofly

import "errors"

var (
	// ErrClientNotSet is returned when a pilot's client reference is not set.
	ErrClientNotSet = errors.New("client reference not set for this pilot")

	// ErrPilotIDNotAvailable is returned when a pilot ID is required but not available.
	ErrPilotIDNotAvailable = errors.New("pilot ID not available for this pilot")
)
