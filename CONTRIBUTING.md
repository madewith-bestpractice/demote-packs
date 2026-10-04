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
of Demote's engines, and macro buttons that run several of them in a row. It's data only: no scripts, no expressions, no
conditionals, and Demote never reads replies. The full format is in
[`schema/pack.schema.json`](schema/pack.schema.json).

### Engines

- **`http`**: each button has a `request` with these fields:
  - `method`: `GET`, `POST` or `PUT`;
  - `url`;
  - optional `headers`;
  - optional `body`, with a `contentType`: `application/json`, `text/plain`,
    `text/xml` or `application/x-www-form-urlencoded`. Only
    `application/json` takes a JSON value; the others take a string;
  - optional `auth`, for HTTP Basic sign-in (see `basic_auth` below):
    ```json
    "auth": { "basic": "{{login}}" }
    ```
    Demote builds the `Authorization: Basic …` header from the variable's
    username and password. Don't also write an `Authorization` header.

  Any 2xx reply counts as success. Requests time out after 8 seconds.
- **`home_assistant`**: each button has a `service`, which runs through the
  user's own Home Assistant sign-in in Demote:
  - `action`, such as `media_player.select_source`;
  - optional `target`;
  - optional `data`.

A button in either engine can instead be a macro, with `steps` (see
[Macro buttons](#macro-buttons)). Every button has exactly one of
`request`, `service` or `steps`.

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
- `basic_auth`: a username plus a secret password, asked as one setting. The
  password is kept like a `secret`. `http` packs only, scope `pack` only, no
  `default`. It can only be used as `"auth": {"basic": "{{id}}"}` on a
  request, never written into a URL, header or body;
- `ha_entity`: picked from the user's Home Assistant, with a `domain`. Home
  Assistant packs only.

**Optional variables**

Add `"optional": true` to let the user leave a variable empty. A button
whose request or service uses an empty optional variable shows as needing
setup and isn't sent; the pack's other buttons work as usual. Use it for a
setting only some buttons need, such as a Sonos player id that only "Switch
to TV" uses.

```json
{ "id": "player_id", "scope": "pack", "type": "text", "optional": true,
  "label": { "en": "Player ID (for Switch to TV)", "es": "ID del reproductor (para Cambiar a TV)" } }
```

In a [macro](#macro-buttons), a step whose button uses an empty optional
variable is skipped, not failed, and the macro's other steps run. That's how
"Start movie" still works in a room with no blinds: the user leaves the
blinds empty and that step is skipped.

Any type can be optional, except a variable written into a URL's host
(the `host` or `port` part of `http://{{host}}:{{port}}/…`). Every request
must have somewhere to go, and the disclosure sheet names it.

**Using a variable**
- Write `{{id}}` in a URL, header value, body, `target` or `data`.
- Demote escapes the value for where it appears: URL-encoded in a URL,
  JSON-escaped in JSON, XML-escaped in a `text/xml` body, and as-is in
  `text/plain`.
- In a JSON value body, a slot always lands inside a JSON string, so
  `"bri": "{{level}}"` sends `"bri": "128"`. When the device needs a real
  number, write the body as a string with `contentType: "application/json"`,
  such as `"{\"bri\":{{level}}}"`, and use a `number` variable.
- In a URL's host, only `host` and `port` variables are allowed.

### Macro buttons

A macro button runs up to 8 steps in order, on the phone, with one tap. It
has `steps` instead of a `request` or `service`:

```json
{ "id": "intermission", "label": { "en": "Intermission", "es": "Intermedio" }, "icon": "pause",
  "steps": [
    { "key": "pause" },
    { "button": "lights_half" }
  ] }
```

**Steps**
- `{"button": "<id>"}` runs another button of the same pack, with that
  button's own settings.
- `{"key": "<name>"}` sends a standard TV key to whichever TV the remote is
  on, exactly as that key's button on the remote does. The TV doesn't need
  to be in Home Assistant. Names come from
  [`schema/keys.json`](schema/keys.json): `power`, `volume_up`,
  `volume_down`, `mute`, `play`, `pause`, `play_pause`, `stop`, `home`,
  `back`, `dpad_up`, `dpad_down`, `dpad_left`, `dpad_right`, `dpad_center`
  (OK), `channel_up`, `channel_down`. `power` and `mute` are toggles, like
  the remote's own buttons.
- Optional `delayMs`, 0 to 5000, default 400: the pause after the step, and
  between its repeats. The last step's pause is skipped.
- Optional `repeat`, 1 to 10, default 1: how many times the step runs, such
  as `{"key": "volume_down", "repeat": 5}`.

The app's macro editor offers pauses of 0, 200, 400, 600, 1000, 1500, 2000
and 3000 ms, and repeats of 1, 2, 3, 4, 5, 8 and 10. Prefer those, so a
customized copy shows the same values.

**Rules** (the validator checks them)
- A step names exactly one of `button` or `key`.
- A `button` step names another button of the same pack that isn't a macro.
  A macro can't run itself or another macro, so there's no nesting or
  looping.
- A macro has no `variables` and no hold-to-`repeat`. Its steps' buttons
  carry the settings.
- At least one step must always run: a TV key, or a button with no
  optional variable. A macro made only of skippable steps could do nothing.

**Settings.** When the user places a macro, Demote asks once for the
settings of every button its steps run. Give the buttons a macro uses clear
setting labels, and make a device that some homes won't have `optional`.
If that button has other settings, make them optional too or give them a
`default`, so the user can leave the whole step empty.

**Placing a macro**
- **Placed as-is**, it stays linked to the pack. Pack updates flow in, and
  it shows "Pack required" if the pack is turned off, like any pack button.
- **Customize** copies it into the user's own macros, unlinked. Its pack
  steps stay pack steps, the user can add their own (such as opening an app
  at the end), and pack updates no longer change it.

Steps run on the phone, one after another, so a macro isn't a Home
Assistant script and needs nothing set up in Home Assistant.

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

## Reporting a problem with a pack

If a pack's button doesn't work, does the wrong thing, or a label is wrong,
open a [problem report](../../issues/new?template=report-a-problem.yml).
Demote's "Report a problem" link on each pack page opens this form with the
pack id and version already filled in. Never include IP addresses,
passwords or keys.

## Requesting a pack

Can't build it yourself? [Request a pack](https://github.com/madewith-bestpractice/demote-packs/issues/new?template=request-a-pack.yml)
with the device or service, its models, a link to its local API docs if you
know one, the buttons you want, and whether you can test on real hardware.
Requests get the `pack request` label.

## Updating a pack

Bump `version`. Don't remove or rename a button `id` that people may have
placed: Demote shows those buttons as "Pack required" rather than guessing.
Add new ids instead. A macro placed as-is picks up changes to its steps, so
change a macro's steps only in ways its users would expect.

## License

By contributing, you agree that your pack is released under this
repository's [MIT license](LICENSE).
