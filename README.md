# Little Oats Homeschool

A comprehensive homeschool curriculum and management platform designed specifically for Texas families.

🌐 **Live Site:** [https://streamline1175.github.io/little-oats-homeschool](https://streamline1175.github.io/little-oats-homeschool)

## About

Little Oats Homeschool is a modern, professional landing page for a Texas-based homeschool application currently under development. The platform will provide:

- 📚 **K-12 Curriculum** - Complete curriculum aligned with Texas TEKS standards
- 📊 **Progress Tracking** - Detailed reports and analytics for each student
- 👨‍👩‍👧‍👦 **Multi-Child Support** - Manage multiple students from one account
- 📅 **Flexible Scheduling** - Customizable lesson plans and calendars
- 📝 **Printable Resources** - Worksheets and materials for offline learning

## Technology Stack

This landing page was built using modern vanilla web technologies for optimal performance:

- **HTML5** - Semantic, accessible markup
- **CSS3** - Custom properties, Grid, Flexbox, modern animations
- **Vanilla JavaScript** - No frameworks, lightweight interactivity
- **Google Fonts** - Playfair Display & Inter for typography

### Why No Framework?

For a landing page focused on:
- ⚡ **Performance** - No JavaScript bundle overhead
- 🔍 **SEO** - Server-rendered, crawlable content
- 🌐 **Accessibility** - Native browser behaviors preserved
- 📱 **Reliability** - Works without JavaScript enabled
- 🚀 **GitHub Pages** - Simple static hosting

## Project Structure

```
little-oats-homeschool/
├── index.html          # Main landing page
├── css/
│   ├── styles.css      # Core styles & design system
│   └── animations.css  # Animation utilities
├── js/
│   └── main.js         # Interactive features
├── assets/
│   └── favicon.svg     # Site favicon
└── README.md           # This file
```

## Features

### Design
- 🎨 Warm, educational color palette
- 📐 Modern design system with CSS custom properties
- 🌊 Smooth scroll-triggered animations
- 📱 Fully responsive (mobile-first)
- ♿ WCAG accessible

### Sections
1. **Hero** - Eye-catching introduction with animated mockup
2. **Features** - Key platform capabilities
3. **Curriculum** - Subject coverage overview
4. **How It Works** - Simple 3-step process
5. **Testimonials** - Social proof from families
6. **Pricing** - Transparent pricing information
7. **Waitlist** - Email signup for early access
8. **FAQ** - Common questions answered

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/Streamline1175/little-oats-homeschool.git
   cd little-oats-homeschool
   ```

2. Open in your browser:
   ```bash
   # Using Python
   python -m http.server 8000
   
   # Using Node.js
   npx serve
   
   # Or simply open index.html in your browser
   ```

3. Visit `http://localhost:8000`

## Deployment

This site is configured for GitHub Pages deployment:

1. Push to the `main` branch
2. Go to repository Settings → Pages
3. Set source to "Deploy from a branch"
4. Select `main` branch and `/ (root)` folder
5. Save and wait for deployment

The site will be available at:
`https://streamline1175.github.io/little-oats-homeschool`

## Customization

### Colors
Edit the CSS custom properties in `css/styles.css`:
```css
:root {
    --color-primary: #2D5A27;      /* Main green */
    --color-accent: #D4A373;       /* Warm accent */
    --color-warm: #FAEDCD;         /* Background warm */
    /* ... */
}
```

### Fonts
Fonts are loaded from Google Fonts in `index.html`. To change:
```html
<link href="https://fonts.googleapis.com/css2?family=YOUR+FONTS" rel="stylesheet">
```

### Content
All content is in `index.html`. Edit text, testimonials, pricing, and FAQs directly.

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License


© 2025 Little Oats Homeschool. All rights reserved.

---

Made with ❤️ in Texas
