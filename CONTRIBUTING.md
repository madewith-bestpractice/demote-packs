# Contributing a button pack

Thanks for building a pack. Every pull request is reviewed by a person
before it's merged, and nothing reaches the Demote app until it's merged.

## The short version

1. Fork this repo and add your pack as `packs/<id>.json`. The `id` is
   reverse-DNS, such as `io.github.yourname.denon-avr`, and the file name
   must match it.
2. Run the checks:
   ```sh
   pip install "jsonschema>=4.18,<5"
   python tools/validate.py packs/<id>.json
   python tools/build_index.py
   ```
3. Commit the pack and the updated `index.json`, then open a pull request.
   Fill in the checklist.

The examples in `examples/` show both engines.

## What a pack is

A pack is a JSON file. It describes buttons that send requests through one
of Demote's engines. It's data only: no scripts, no expressions, no
conditionals, and Demote never reads replies. The full format is in
[`schema/pack.schema.json`](schema/pack.schema.json).

### Engines

- **`http`**: each button has a `request` with these fields:
  - `method`: `GET`, `POST` or `PUT`;
  - `url`;
  - optional `headers`;
  - optional `body`, with a `contentType`.

  Any 2xx reply counts as success. Requests time out after 8 seconds.
- **`home_assistant`**: each button has a `service`, which runs through the
  user's own Home Assistant sign-in in Demote:
  - `action`, such as `media_player.select_source`;
  - optional `target`;
  - optional `data`.

### Metadata

| Field | Rules |
|---|---|
| `name` | At most 32 characters. Shown on the pack's tile and its builder category. |
| `description` | One sentence, at most 120 characters. |
| `vendor` | The hardware or service the pack controls. |
| `author` | You. Shown as "Community pack · by <author>". |
| `icon` | A name from [`schema/icons.json`](schema/icons.json). Packs can't ship images. |
| `accent` | Optional, from a fixed palette. |

The button list users see comes straight from `buttons`. Each label is at
most 24 characters.

Text fields take a language map. `en` is required. Add `es` and other
languages if you can; English is the fallback.

### Variables

Anything that differs between homes is a variable, never hard-coded: an IP
address, a key, an input name.

**Scopes**
- `"scope": "pack"`: asked once, when the user turns the pack on. Use this for
  the device's address or an API key.
- `"scope": "button"`: asked when the user places that button. Use this for
  things like which input to switch to.

**Types**
- `text`, `number` (with `min` and `max`), `choice` (with `options`),
  `host`, `port`;
- `secret`: masked, stored in the phone's secure storage, and never included
  when buttons are copied or shared;
- `ha_entity`: picked from the user's Home Assistant, with a `domain`. Home
  Assistant packs only.

**Using a variable**
- Write `{{id}}` in a URL, header value, body, `target` or `data`.
- Demote escapes the value for where it appears: URL-encoded in a URL,
  JSON-escaped in JSON.
- In a URL's host, only `host` and `port` variables are allowed.

### Network

- **`"network": "local"`** is the default. The pack may only reach private,
  link-local or `.local` addresses, and Demote enforces this when a button is
  pressed.
- **`"network": "internet"`** is for cloud services. These packs get a
  stronger disclosure in the app and a closer review here.

Requests are only ever sent when the user presses a button, or presses Test
in the builder.

## Review

Before merging, a reviewer checks that:

- the pack does what its name and description say;
- the endpoints are real, with a link to the vendor's documentation;
- every button was tested on real hardware or the real service;
- requests go only to the vendor's device or service, never to analytics or
  tracking hosts;
- nothing private is in the file;
- labels are clear, and trademarks appear only in `vendor`.

We may ask for changes, or decline packs that duplicate a better one or
control something unsafe to trigger by accident, such as door locks or
alarms.

## Updating a pack

Bump `version`. Don't remove or rename a button `id` that people may have
placed: Demote shows those buttons as "Pack required" rather than guessing.
Add new ids instead.

## License

By contributing, you agree that your pack is released under this
repository's [MIT license](LICENSE).
