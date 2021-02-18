// https://create-react-app.dev/docs/proxying-api-requests-in-development/#configuring-the-proxy-manually

const proxy = require("http-proxy-middleware");

module.exports = function (app) {
  app.use(
    "/api",
    proxy({
      target: window.DIAAS.API_BASEURL,
      changeOrigin: true,
    })
  );
};
