// Adds a simplified "Is this a mobile device?" test to Modernizer. This covers all older tablets and phones, plus
// the iPad Pro, without (hopefully) picking up any laptops.
if (Modernizr) {
  Modernizr.addTest(
    'mobile',
    Modernizr.touch && Modernizr.mq("(max-width: 1024px), (max-width: 1366px) and (min-device-pixel-ratio: 2.0)")
  );
}
