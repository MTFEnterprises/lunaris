# Relay Scenario Design Note

**Status:** Design only. No relay scenario is currently calculated by LUNARIS.

## Purpose

A lunar relay could provide an alternate path when a landing site cannot see
Earth directly. A relay opportunity is not an end-to-end communication link:
site-to-relay visibility, relay-to-Earth visibility, radio capability, antenna
constraints, and Earth-station availability all need to be established.

## Required inputs

An eventual implementation must use a cited source or explicit scenario input
for every item below. Missing inputs remain unavailable; no orbit or capability
is assumed.

- Relay ephemeris with timestamps, coordinate frame, units, source, coverage,
  and retrieval/version metadata.
- Site coordinates and, where available, a validated terrain horizon profile.
- Relay-to-Earth geometry over the same UTC time grid.
- User-supplied radio parameters and antenna boresight/pointing constraints for
  each link.
- Any operational schedule or station-availability data used to claim
  end-to-end service.

## Future calculation boundary

For each time step, evaluate site-to-relay geometric line of sight in the
declared body-fixed frame. When a valid terrain horizon is present, report
terrain-corrected visibility separately. Evaluate relay-to-Earth visibility
and each RF budget independently. An end-to-end opportunity may only be
reported where both links are available at the same time and all required
operational inputs are present.

The result should keep geometric visibility, terrain visibility, and modeled
RF link status as separate fields. It should include provenance for each
ephemeris and terrain input, assumptions for each link budget, and warnings
for unavailable inputs. A relay path must not be described as available merely
because the site can see the relay.

## Current limitations

This repository does not provide a cited relay trajectory, relay hardware
parameters, relay schedule, or Earth-station schedule. Therefore no relay
availability, coverage, or performance numbers are published here.

## Acceptance checks before implementation

- Validate at least one sourced or explicitly user-defined relay trajectory
  against an independent reference.
- Test clear line of sight and lunar-body occultation with analytic geometry.
- Test that a valid terrain horizon can further block site-to-relay visibility.
- Test that missing relay or Earth-link inputs produce unavailable results,
  not a fabricated end-to-end window.
- Keep all times UTC and all vectors in one documented frame.
