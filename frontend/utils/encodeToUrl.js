// Given a string, encode it to a URL friendly string and escape special characters
// Returns the encoded string
const encodeToUrl = (str) => {
  return encodeURIComponent(str).replace(/%20/g, "+");

};



