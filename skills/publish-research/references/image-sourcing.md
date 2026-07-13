# Image sourcing and embedding

Use this guide for the image pass after the article copy and structure have passed factual review. The configured `images.mode` decides whether images are hotlinked, stored with the page, or replaced with placeholders.

## Image scope

Source one image for each distinct recommendation and runner-up, normally 5-7 products. Reuse those images in the hero, TL;DR rows, comparison matrix, pick cards, runner-up blocks, and matching all-products cards. Do not spend time sourcing new images for every rejected candidate.

The best pick's image can also serve as the hero image when it has a clean background and enough resolution.

## Modes

### `hotlink`

Reference the validated retailer or manufacturer image URL directly.

Every remote image must include:

```html
loading="lazy" referrerpolicy="no-referrer"
```

Escape `&` as `&amp;` inside HTML attributes.

Hotlinking keeps the repository small but is fragile. Retailers can change URLs, block embedding, or remove products. Check the source site's terms before publishing. A successful browser check today does not guarantee long-term availability.

### `local`

Download validated images to:

```text
<outputDirectory>/<slug>/images/
```

Use short, stable filenames derived from the model name and preserve the real image extension. Reference them with relative URLs such as `images/model-name.webp`.

Local storage is more reliable, but the publisher is responsible for image licensing, attribution, and repository size.

### `placeholder`

Remove the optional hero image block. Use the existing `.allp__media--placeholder` pattern for product cards and an equivalent placeholder or no image for picks, TL;DR rows, and matrix columns. Do not leave `{{..._IMG_URL}}` markers behind.

## Source ladder

Start from the product or retailer links already present in the research. Prefer, in order:

1. The manufacturer product page.
2. The retailer page cited in the recommendation.
3. Another reputable retailer carrying the exact same model and configuration.
4. A marketplace product page only when the seller and model are clear.

For a normal HTML product page, inspect `og:image` first. The URL and every redirect must use HTTP or HTTPS and a public host; do not request localhost, loopback, link-local, or private-network addresses.

```bash
curl -sL --proto '=http,https' --proto-redir '=http,https' --max-time 20 -A "Mozilla/5.0" "<product-url>" \
  | grep -oiE '<meta[^>]+og:image[^>]*content="[^"]+"'
```

If that image is a logo, banner, low-resolution crop, or lifestyle photo with a busy background, inspect the product gallery instead.

Common storefront patterns:

- WooCommerce: look for `data-large_image` or the largest product-gallery upload.
- Shopify: prefer product, flat, or front-on-white gallery variants over lifestyle shots.
- Magento: prefer the full `/media/catalog/product/` path over cached thumbnails.
- OpenCart: inspect whether the URL contains a small crop suffix.
- JavaScript-rendered shops: use browser inspection when available, or find the exact model on another reputable retailer.

Market-specific retailers are examples, not defaults. For Romanian product research, eMAG often exposes clean product images in static metadata, but the publishing workflow must not assume Romanian availability or an eMAG listing for every run.

## Validate every image

Never trust a generated or search-result image URL without fetching it.

For a remote image:

```bash
curl -sL --proto '=http,https' --proto-redir '=http,https' --max-time 25 -A "Mozilla/5.0" -o /tmp/publish_research_image "<image-url>"
file /tmp/publish_research_image
```

The file must be a real JPEG, PNG, or WebP, not HTML. View it and confirm:

- the exact product, model, size, and color are correct
- the image is not a logo, banner, category tile, or unrelated variant
- resolution is sufficient for its largest placement
- the background works with the configured design

Generated research tools can invent plausible CDN filenames. Use them to find product pages, never as authority for an image URL.

## Template insertion points

Fill or replace the image slots already present in `page-template.html`.

Hero, using the best pick:

```html
<div class="hero__media"><img src="URL" alt="NAME" loading="lazy" referrerpolicy="no-referrer"></div>
```

TL;DR row, with the thumbnail as the first child and the tier inside `.tldr__main`:

```html
<a class="tldr__row" href="#pick-best">
  <span class="tldr__thumb"><img src="URL" alt="NAME" loading="lazy" referrerpolicy="no-referrer"></span>
  <div class="tldr__main">
    <span class="tldr__tier tldr__tier--best">Best</span>
    <div class="tldr__name">NAME</div>
    <div class="tldr__why">WHY</div>
  </div>
  <div class="tldr__price">PRICE</div>
</a>
```

Pick banner:

```html
<div class="pick__media"><img src="URL" alt="NAME" loading="lazy" referrerpolicy="no-referrer"></div>
```

Runner-up thumbnail:

```html
<span class="pick__runner-media"><img src="URL" alt="NAME" loading="lazy" referrerpolicy="no-referrer"></span>
```

All-products card, reusing a pick or runner-up image:

```html
<div class="allp__media"><img src="URL" alt="NAME" loading="lazy" referrerpolicy="no-referrer"></div>
```

All other cards use:

```html
<div class="allp__media allp__media--placeholder"><span>No image</span></div>
```

Comparison matrix, reusing each pick image:

```html
<img class="matrix__img" src="URL" alt="NAME" loading="lazy" referrerpolicy="no-referrer">
```

The image pass must not edit editorial copy or shared CSS.

## Browser verification

Serve the configured output directory locally and inspect the page at desktop and 375px mobile widths. Scroll through the full page and all-products carousel so lazy images load.

Confirm:

- every expected image loads
- no image is the wrong product or variant
- the hero does not look like a hard rectangular ad inside the page
- TL;DR thumbnails do not crowd model names or prices
- runner-up images and carousel cards do not overlap text
- local image paths survive a nested `<slug>/index.html` URL

Close browser sessions and local servers after verification.

## Report

Return a per-product list with the chosen source, mode, final URL or path, and validation result. Note placeholders, failed sources, licensing concerns, and any checks that still need a human browser pass.
