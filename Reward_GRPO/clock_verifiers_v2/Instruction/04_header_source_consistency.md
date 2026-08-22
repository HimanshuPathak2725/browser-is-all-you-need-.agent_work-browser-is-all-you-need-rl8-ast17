# C04 instruction: header/source consistency

## Observed failure

Trial a5 defined constructors and used `_minute` in `clock.cpp` without corresponding class declarations. Seven diagnostics descended from two declaration defects.

## Contract

The public header, implementation file, and externally compiled caller must agree. Every out-of-class definition must match a declaration, and every state access must belong to the declared class.

## Kernels

| Kernel | Pass condition |
| --- | --- |
| C04-A | Candidate implementation compiles independently |
| C04-B | External factory/arithmetic caller links against it |
| C04-C | All public methods compose across the header/source boundary |

Private field names and representation are not inspected; only compiler/linker-visible consistency is scored.
