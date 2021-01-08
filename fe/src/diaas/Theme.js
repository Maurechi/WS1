import {
  ThemeProvider as MUIThemeProvider,
  unstable_createMuiStrictModeTheme as createMuiTheme,
} from "@material-ui/core/styles";

const COLORS = {
  DARK_BLUE: "#001142",
  PURPLE: "#9611F5",
  AQUAS: "#13C6F7",
  WHITE: "#EEEEEE",
};

const theme = createMuiTheme({
  palette: {
    background: { main: COLORS.DARK_BLUE },
    foreground: { main: COLORS.WHITE },
    primary: { main: COLORS.AQUAS },
    secondary: { main: COLORS.PURPLE },
  },
});

export const ThemeProvider = ({ children }) => <MUIThemeProvider theme={theme}>{children}</MUIThemeProvider>;
