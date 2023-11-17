# List of things to do for the library

## Better input description for plaquette indices

Currently, plaquette indices are given as lists of integers. This is problematic because the user have no clue about which index is going where on the final plaquette. 

This could be circumvented by having easily-accessible examples for each plaquette templates, but it will quickly become impossible to show large examples (even a distance 4 corner is already quite a mess to look at).

## Verification of templates

Verification of templates should be quite easy once the interface for the plaquettes will be defined. For example, any instance of `Template` could have a `check_validity` method that would take as input the plaquette data-structure instances and that would output either a validation (i.e., the template is valid) or an error explaining why the template failed the verification.

