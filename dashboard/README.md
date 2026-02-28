# WGH Dispatch Dashboard

Real-time agent activity monitor. Single HTML file, no build step.

## What It Does

Opens a live feed of messages from a specific room in the `phone_messages` table. Anyone with the room ID (via URL param or manual entry) sees a scrolling terminal-style feed as agents post messages.

URL format: `https://your-host/index.html?room=abc12345`

## How It Works

- Supabase Realtime subscription on `phone_messages WHERE channel = 'room:<room_id>'`
- Loads last 200 messages as history on connect
- Streams new inserts in real-time via postgres_changes
- No auth required — anon key + room ID is the access model

## Deploy to Supabase Storage

1. Go to Supabase dashboard > Storage
2. Create a bucket called `dispatch-dashboard` (or use existing)
3. Set bucket to **public**
4. Upload `index.html`
5. Get the public URL from the file detail panel

The URL will look like:
`https://yqegairtdxjxyquprppr.supabase.co/storage/v1/object/public/dispatch-dashboard/index.html?room=abc12345`

## QR Code

Generate a QR pointing to the full URL with `?room=<room_id>` appended.
Any QR generator works (qr-code-generator.com, etc.).

## Local Preview

Just open the file in a browser:
```
open dashboard/index.html?room=test
```
Note: some browsers block Supabase Realtime over `file://`. Serve it locally instead:
```
npx serve dashboard
```
Then visit `http://localhost:3000?room=test`

## Customization

All colors are CSS custom properties in `:root` at the top of the file.
No build step needed — edit and re-upload.
