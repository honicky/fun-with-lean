// CloudFront Function (viewer-request) that maps "pretty" URLs to the
// index.html objects produced by Astro's `directory` build format:
//   /miratyper      -> /miratyper/index.html
//   /miratyper/     -> /miratyper/index.html
//   /assets/app.css -> unchanged (has a file extension)
function handler(event) {
  var request = event.request;
  var uri = request.uri;

  if (uri.endsWith("/")) {
    request.uri = uri + "index.html";
  } else if (!uri.includes(".")) {
    request.uri = uri + "/index.html";
  }
  return request;
}
