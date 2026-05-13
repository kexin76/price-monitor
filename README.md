# Gunpla Monitor
Gunpla Price/Website Monitor for Gundam Planet and USA Gundam Store

## Environment Variables
- "MY_GMAIL" , User's gmail
- "APP_PASSWORD", Enable 2 steps verification per user's profile, then go to 
```https://myaccount.google.com/apppasswords``` to generate app password

## Config File
Settings: 
- check_interval_seconds, How many seconds till the next cycle to monitor websites.
- reset_seenproducts_every_cycle, Whether to reset seen_products per cycle

Budget:

- Keywords or grades for the model kits, along with the minimum and maximum price for each grade.

Watch list:

- A list of URLs of individual items with the website the product is from.

GundamPlanet:

- The base url, which contains all gunpla products.
- Limits for how many products to load per page.

USA Gundam Store:

- Collections of URLs for different categories, can add more URLs for more gunpla categories.