module.exports = {
  extends: ["eslint:recommended", "react-app", "prettier"],
  plugins: ["simple-import-sort", "unused-imports"],
  rules: {
    "no-duplicate-imports": "error",
    "no-loop-func": "error",
    "array-callback-return": "error",
    "no-var": "error",
    "no-unused-vars": "off",
    "unused-imports/no-unused-imports": 2,
    "unused-imports/no-unused-vars": 1,
    "simple-import-sort/sort": [
      "error",
      {
        groups: [["^(?!\\u0000?(?:diaas|[.])/)"]],
      },
    ],
    "sort-imports": "off",
    "import/order": "off",
  },
  globals: {},
};
