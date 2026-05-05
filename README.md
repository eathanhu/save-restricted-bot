<h1>Telegram Clone Bot (jam.py)</h1>

<p>
  A private/public Telegram message cloning bot built with <b>Pyrogram</b> + <b>Pyromod</b>.
  It supports protected/private source links using a user <code>STRING_SESSION</code>,
  uploads to Log Channel 1 as the base destination, supports optional Log Channel 2 and DM forwarding,
  and includes per-user filters and private download/upload progress.
</p>

<hr />

<h2>Features</h2>
<ul>
  <li>Clone message ranges from Telegram links (<code>t.me/public/123</code> and <code>t.me/c/private/123</code>).</li>
  <li>Private/restricted cloning using user session (<code>STRING_SESSION</code>).</li>
  <li>Single-message mode using <code>?single</code> or <code>&amp;single</code>.</li>
  <li>Single-file rename flow using <code>-r</code> or <code>-rename</code>.</li>
  <li>Media-type filters: video, photo, document, audio, voice, gif, sticker, text.</li>
  <li>Per-user delivery settings from inline UI (<code>/settings</code>).</li>
  <li>Log Channel 1 is base destination; DM forwarding happens from Log1 when enabled.</li>
  <li>Private download/upload progress status (speed, ETA, processed bytes, percent bar).</li>
  <li>Owner user management commands: <code>/adduser</code>, <code>/removeuser</code>, <code>/users</code>.</li>
  <li>Cancelable clone task with inline <b>Cancel</b> button.</li>
</ul>

<hr />

<h2>Supported Link Types</h2>
<ul>
  <li><code>https://t.me/channel_username/123</code> (public)</li>
  <li><code>https://t.me/c/1234567890/123</code> (private/restricted)</li>
  <li><code>https://t.me/b/botusername/123</code> (bot-style private format)</li>
</ul>

<hr />

<h2>Commands</h2>
<ul>
  <li><code>/clone</code> - Start clone flow (interactive or with inline link).</li>
  <li><code>/settings</code> - Open delivery/filter controls.</li>
  <li><code>/adduser USER_ID</code> - Owner only.</li>
  <li><code>/removeuser USER_ID</code> - Owner only.</li>
  <li><code>/users</code> - Owner only.</li>
</ul>

<hr />

<h2>Clone Usage</h2>

<h3>Normal Range Clone</h3>
<pre><code>/clone https://t.me/channel/100</code></pre>
<p>Then bot asks for END link.</p>

<h3>Single Message Clone</h3>
<pre><code>/clone https://t.me/channel/100?single</code></pre>

<h3>Single File Rename Clone</h3>
<pre><code>/clone https://t.me/channel/100 -r</code></pre>
<p>Then bot asks for new file name and uploads using download+upload flow.</p>

<hr />

<h2>Progress UI (Private/Restricted)</h2>
<pre><code>{filename}

Task By:{username}
┟ [⬡⬡⬡⬡⬡⬡⬡⬡⬡⬡⬡⬡] 0.0%
┠ Processed → 0B of 0B
┠ Status → Resolving / Download / Upload / Waiting
┠ Speed → 0B/s
┠ ETA → - -
</code></pre>

<hr />

<h2>Configuration</h2>
<p>
  <b>Recommended:</b> Use environment variables on VPS.<br />
  The script also has fallback defaults inside code, but env vars are safer and cleaner.
</p>

<pre><code>API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH
BOT_TOKEN=YOUR_BOT_TOKEN
OWNER_ID=YOUR_TELEGRAM_USER_ID
STRING_SESSION=YOUR_USER_SESSION_STRING
</code></pre>

<p>Core runtime values used by the bot:</p>
<ul>
  <li><code>LOG_CHANNEL_1</code> - Base destination (username or chat id).</li>
  <li><code>LOG_CHANNEL_2</code> - Optional second destination.</li>
  <li><code>CUSTOM_CAPTION</code> - Caption tag appended to media/text.</li>
  <li><code>CLONE_DELAY</code> - Delay between messages in range cloning.</li>
</ul>

<hr />

<h2>Requirements</h2>
<ul>
  <li>Python 3.10+</li>
  <li>Telegram Bot Token from <code>@BotFather</code></li>
  <li>Telegram API credentials from <code>my.telegram.org/apps</code></li>
  <li>Valid user <code>STRING_SESSION</code> for private/restricted sources</li>
  <li>Bot must be admin/post-enabled in target log channel(s)</li>
</ul>

<hr />

<h2>Install (Local or VPS)</h2>
<pre><code>sudo apt update
sudo apt install -y python3 python3-pip screen

mkdir -p ~/jam-bot
cd ~/jam-bot

# place jam.py here

pip3 install -U pyrogram tgcrypto pyromod
</code></pre>

<hr />

<h2>Run with Screen (VPS Deployment)</h2>

<h3>1) Start a screen session</h3>
<pre><code>screen -S jambot</code></pre>

<h3>2) Export environment variables</h3>
<pre><code>export API_ID="YOUR_API_ID"
export API_HASH="YOUR_API_HASH"
export BOT_TOKEN="YOUR_BOT_TOKEN"
export OWNER_ID="YOUR_OWNER_ID"
export STRING_SESSION="YOUR_STRING_SESSION"
</code></pre>

<h3>3) Run bot</h3>
<pre><code>python3 jam.py</code></pre>

<h3>4) Detach screen</h3>
<pre><code>Ctrl + A, then D</code></pre>

<h3>5) Re-attach later</h3>
<pre><code>screen -r jambot</code></pre>

<h3>6) List sessions</h3>
<pre><code>screen -ls</code></pre>

<hr />

<h2>Troubleshooting</h2>

<h3>1) <code>sqlite3.OperationalError: database is locked</code></h3>
<p>Another process is using the same session file.</p>
<pre><code>pkill -f "python3 jam.py"
rm -f bot_runner.session-journal bot_runner.session-wal bot_runner.session-shm
rm -f user_runner.session-journal user_runner.session-wal user_runner.session-shm
python3 jam.py
</code></pre>

<h3>2) <code>Peer id invalid</code> (private source)</h3>
<ul>
  <li>STRING_SESSION account is not joined in that private channel/chat.</li>
  <li>Link chat id is wrong.</li>
  <li>Session expired/revoked and must be regenerated.</li>
</ul>

<h3>3) <code>ACCESS_TOKEN_INVALID</code></h3>
<p>Bot token is wrong/revoked. Regenerate from <code>@BotFather</code>.</p>

<h3>4) Log channel send failures</h3>
<ul>
  <li>Bot not admin in Log1/Log2 channel.</li>
  <li>Bot has no post permissions.</li>
  <li>Wrong channel id/username.</li>
</ul>

<hr />

<h2>How Destinations Work</h2>
<ul>
  <li>Log Channel 1 is the primary/base destination.</li>
  <li>If Log2 is enabled, same message/file also goes there.</li>
  <li>If DM is enabled, user receives forwarded copy from Log1 message (not direct fallback copy).</li>
</ul>

<hr />

<h2>Security Notes</h2>
<ul>
  <li>Do not expose <code>BOT_TOKEN</code> or <code>STRING_SESSION</code> in public repos.</li>
  <li>Use environment variables in production.</li>
  <li>If leaked, rotate token/session immediately.</li>
</ul>

<hr />

<h2>Tech Stack</h2>
<ul>
  <li>Python</li>
  <li>Pyrogram</li>
  <li>Pyromod</li>
  <li>TgCrypto</li>
</ul>

<hr />

<h2>License</h2>
<p>Use responsibly and follow Telegram Terms and your local laws.</p>
