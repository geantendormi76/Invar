# Configuration Injection Contract

`configs/` is the single declarative configuration layer of the repository.
Product code must not scatter environment-specific constants across source files.

## Precedence

The intended merge order is:

`base -> profile -> local -> environment -> CLI`

Later layers override earlier layers. A runtime must expose the resolved configuration
as a typed object before entering domain logic.

## Directories

- `base/`: committed defaults and stable contracts.
- `profiles/`: named runtime profiles such as `dev`, `research`, `offline`, `prod`.
- `local/`: machine-specific overrides; never commit secrets here.
- `examples/`: safe templates that can be copied into `local/`.
- `schemas/`: validation schemas and compatibility contracts.
- `registry/`: model/backend/provider/plugin registration metadata.

## Hot-plug rule

Adding or replacing an implementation should normally require:

1. implementing the stable Rust/Python interface;
2. registering the implementation by an explicit identifier;
3. selecting it through configuration.

The orchestration layer should not contain implementation-specific path checks,
filename checks, magic numbers, or provider-specific branches.

Secrets belong in environment variables or an OS secret store, not in tracked TOML files.
