## What this pack does

<!-- One or two sentences. Which device or service, and which buttons. -->

## Checklist

- [ ] The pack is in `packs/<id>.json`, and `python tools/validate.py` passes.
- [ ] I ran `python tools/build_index.py` and committed the updated `index.json`.
- [ ] I tested every button on real hardware or a real service (model and firmware: …).
- [ ] If the pack has macros: I ran each one end to end, and again with its optional settings left empty.
- [ ] Every request goes only to the device or service named in `vendor`. Nothing goes to analytics or tracking hosts.
- [ ] Links to the vendor's documentation for the endpoints used: …
- [ ] Nothing private is in the file: no keys, tokens, passwords or personal addresses. Anything private is a `secret` or `host` variable.
- [ ] Labels are short and clear, and the pack name doesn't use a trademark except in `vendor`.
- [ ] I agree to license this pack under the repository's MIT license.
