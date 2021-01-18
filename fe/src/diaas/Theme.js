import {
  ThemeProvider as MUIThemeProvider,
  unstable_createMuiStrictModeTheme as createMuiTheme,
} from "@material-ui/core/styles";

const COLORS = {
  DARK_BLUE: "#001142",
  NOT_SO_DARK_BLUE: "#404a6b",
  PURPLE: "#9611F5",
  AQUAS: "#13C6F7",
  WHITE: "#EEEEEE",
};

const theme = createMuiTheme({
  palette: {
    background: { main: COLORS.DARK_BLUE, light: COLORS.NOT_SO_DARK_BLUE },
    foreground: { main: COLORS.WHITE },
    primary: { main: COLORS.PURPLE, contrastText: "#ffffff" },
    secondary: { main: COLORS.AQUAS },
  },
});

export const ThemeProvider = ({ children }) => <MUIThemeProvider theme={theme}>{children}</MUIThemeProvider>;
