⛓️ ChainMe — Spell Your Name in Crypto
========================================

**ChainMe** is a vibrant, interactive crypto name generator website that transforms your name into iconic cryptocurrency symbols. Watch as 26 crypto symbols burst from the center and float endlessly in the background, then enter your name to reveal each letter as its corresponding crypto coin card.

## Features

✨ **Opening Animation** — All 26 crypto symbols burst from the center with a mesmerizing spiral explosion, then settle into floating positions and drift continuously across the background

🎴 **Flip Card Reveal** — Type your name and watch as black tiles flip one by one, revealing the crypto symbols for each letter with smooth 3D animations and satisfying tick sound effects

📥 **Downloadable Images** — Generate a high-quality PNG image of your name chain with ChainMe branding, perfect for sharing on social media

🐦 **Social Sharing** — One-click share to X (Twitter) with pre-filled message and crypto hashtags, or copy your name chain to clipboard

📖 **Alphabet Reference** — Explore all 26 crypto mappings in an elegant collapsible legend panel

🎉 **Confetti Burst** — Colorful confetti animation celebrates when your name is fully revealed

📱 **Mobile Responsive** — Fully optimized for all screen sizes, from desktop to mobile

## How to Use

1. **Open** — Simply open `index.html` in any modern web browser (no server required)
2. **Enter** — Type your name in the input field (letters A-Z only)
3. **Generate** — Click the "Generate ⚡" button or press Enter to reveal your crypto chain
4. **Download** — Once revealed, download your name as a branded PNG image
5. **Share** — Share your chain on X or copy it to clipboard
6. **Regenerate** — Click "New Name" to try another combination

## Tech Stack

- **HTML5** — Semantic markup
- **CSS3** — Animations, glassmorphism, 3D transforms, gradients
- **Vanilla JavaScript** — No frameworks or build tools
- **Canvas API** — Image generation and download
- **Web Audio API** — Procedurally generated tick sound effects
- **CSS Transforms & Keyframes** — Burst animation, flip effects, floating drift
- **Google Fonts** — Orbitron (headings) and Space Grotesk (body)

## Browser Support

Works in all modern browsers:
- Chrome/Edge 88+
- Firefox 87+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## File Structure

```
index.html   ← Complete single-page app (HTML + CSS + JavaScript)
README.md    ← This file
```

## Crypto Alphabet Mapping

Each letter corresponds to an iconic cryptocurrency:

| Letter | Ticker | Name | Color |
|--------|--------|------|-------|
| A | ADA | Cardano | #0033AD |
| B | BTC | Bitcoin | #F7931A |
| C | CRO | Cronos | #002D74 |
| D | DOGE | Dogecoin | #C2A633 |
| E | ETH | Ethereum | #627EEA |
| F | FIL | Filecoin | #0090FF |
| G | GRT | The Graph | #6F4CBA |
| H | HBAR | Hedera | #00B388 |
| I | ICP | Internet Computer | #29ABE2 |
| J | JUP | Jupiter | #C4884C |
| K | KAS | Kaspa | #49EACB |
| L | LTC | Litecoin | #BFBBBB |
| M | MKR | MakerDAO | #1AAB9B |
| N | NEO | NEO | #58BF00 |
| O | OP | Optimism | #FF0420 |
| P | POL | Polygon | #8247E5 |
| Q | QTUM | Qtum | #2895D8 |
| R | RENDER | Render Network | #FF4500 |
| S | SOL | Solana | #9945FF |
| T | TRX | TRON | #FF0013 |
| U | UNI | Uniswap | #FF007A |
| V | VET | VeChain | #15BDFF |
| W | WLD | Worldcoin | #888888 |
| X | XRP | Ripple | #00AAE4 |
| Y | YFI | Yearn Finance | #006AE3 |
| Z | ZEC | Zcash | #F4B728 |

## Design System

- **Primary Background** — #0a0a0f (near black)
- **Primary Accent** — #F7931A (Bitcoin orange)
- **Secondary Accent** — #627EEA (Ethereum purple-blue)
- **Glassmorphism** — Frosted glass with backdrop blur and subtle border glow
- **Typography** — Orbitron for headings/tickers (geometric, crypto-style), Space Grotesk for body
- **Animation** — CSS keyframes with easing, Web Animations API, 3D CSS transforms

## Key Animations

🌪️ **Burst Animation** (1s) — Symbols explode outward from center with ease-out timing
⛅ **Float Animation** (infinite) — Gentle continuous drift with subtle rotation
🎴 **Flip Animation** (500ms) — 3D card rotation with staggered timing per letter
✨ **Glow Pulse** (800ms) — Soft glow cascades across cards after reveal
🎆 **Confetti** (2.5s) — Colorful particles fall with rotation

## Customization

Want to modify ChainMe? It's all in one file:

- **Change colors** — Edit the `cryptoAlphabet` object for different coin colors or replace the gradient
- **Adjust animation speeds** — Modify CSS `@keyframes` durations and JS animation delays
- **Customize fonts** — Replace Orbitron/Space Grotesk in Google Fonts link and CSS
- **Add more symbols** — Extend `cryptoAlphabet` with additional letters or cryptocurrencies
- **Modify canvas image** — Edit `generateCanvasImage()` for different download layout

## Performance

- **No external dependencies** (except Google Fonts)
- **Lightweight** — Single HTML file, ~45KB uncompressed
- **Smooth animations** — GPU-accelerated CSS transforms and 3D effects
- **Responsive canvas** — Auto-scales based on name length
- **Web Audio** — Efficient procedural sound generation (no audio files)

## Future Ideas

- Dark/light theme toggle
- More cryptocurrency options
- Custom symbol mapping
- Animated GIF export
- Real-time preview
- Name statistics and crypto correlation
- Export as SVG

## Screenshots

*(Add screenshots of your generated chains here after deploying)*

---

Built with ❤️ for the crypto community

**ChainMe** — Because your name deserves to be on the blockchain ⛓️⚡
