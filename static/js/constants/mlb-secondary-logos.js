// MLB Teams that should use white logos when dynamicColors is enabled
// Teams listed here will use their white logo from /assets/logos/mlb-white/
// White logos should use the same filename as the regular logo
// Special cases can override the filename mapping

const mlbUseWhiteLogos = [
  'Red Sox',
  'Royals', 
  'Athletics',
  'White Sox',
  'Dodgers',
  'Cardinals',
  'Rockies',
  'Tigers',
  'Yankees',
  'Rays',
];

// Special filename mappings for teams that don't follow the standard naming
const mlbWhiteLogoOverrides = {
  'Astros': 'astros-light',  // Uses astros-light.png instead of astros.png
};
