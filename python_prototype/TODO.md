# List of things to do for the library

## Better input description for plaquette indices

Currently, plaquette indices are given as lists of integers. This is problematic because the user have no clue about which index is going where on the final plaquette. 

This could be circumvented by having easily-accessible examples for each plaquette templates, but it will quickly become impossible to show large examples (even a distance 4 corner is already quite a mess to look at).

## Verification of templates

Verification of templates should be quite easy once the interface for the plaquettes will be defined. For example, any instance of `Template` could have a `check_validity` method that would take as input the plaquette data-structure instances and that would output either a validation (i.e., the template is valid) or an error explaining why the template failed the verification.

## [Should be done] Think about unit squares

Currently, two neighbouring templates have to share a dimension. In particular, this means that the 1x1 squares are in a strange position. MEven if most of them can be encoded naturally, even with the current limitations, some cases cannot. 

Examples of cases that are outside of the current limitations:
1. the 1x1 square located inside the corner shape,
2. the two 1x1 squares in the W shape that are in a similar place as the problematic 1x1 square in the corner (see previous point),
3. the two 1x1 squares in the donut shape that are top right and bottom left of the inside empty square.

For the moment, a hack is to virtually extend their size with empty cells, potentially overlapping with other empty cells. This seems sufficient to encode the L shape, but is not to encode the W or donut shape.

A real, realist and already doable fix to that is to require users to create their own template if its is not already in the template library and if they need to. For the examples above:
1. done by a 2x2 instance of `FixedRaw` with 3 empty plaquettes,
2. can be done with the definition of a new template,
2. can be done with the definition of a new template.
