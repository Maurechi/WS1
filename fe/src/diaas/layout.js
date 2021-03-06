import {
  AppBar as MUIAppBar,
  Box,
  Button,
  Divider,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Menu,
  SvgIcon,
  Toolbar,
  Typography,
} from "@material-ui/core";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import AccountCircleIcon from "@material-ui/icons/AccountCircle";
import ArrowDropDownIcon from "@material-ui/icons/ArrowDropDown";
import BuildIcon from "@material-ui/icons/Build";
import DoubleArrowIcon from "@material-ui/icons/DoubleArrow";
import GetAppIcon from "@material-ui/icons/GetApp";
import SearchIcon from "@material-ui/icons/Search";
import SettingsIcon from "@material-ui/icons/Settings";
import StorageIcon from "@material-ui/icons/Storage";
import clsx from "clsx";
import { observer } from "mobx-react-lite";
import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import v from "voca";

import appBarGraphic from "./AppBarGraphic.png";
import { ReactComponent as DataNodesIconSvg } from "./DataNodesIcon.svg";
import { useLocalStorage } from "diaas/form.js";
import { useAppState } from "diaas/state";
import { HCenter } from "diaas/ui.js";
const drawerWidth = 240;

const useStyles = makeStyles((theme) => ({
  root: {
    display: "flex",
  },
  appBar: {
    zIndex: theme.zIndex.drawer + 1,
    transition: theme.transitions.create(["width", "margin"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    backgroundColor: theme.palette.background.main,
    color: theme.palette.foreground.main,
  },
  appBarShift: {
    transition: theme.transitions.create(["width", "margin"], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  menuButton: {
    marginRight: 36,
  },
  hide: {
    display: "none",
  },
  drawer: {
    width: drawerWidth,
    flexShrink: 0,
    whiteSpace: "nowrap",
  },
  drawerOpen: {
    width: drawerWidth,
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  drawerClose: {
    transition: theme.transitions.create("width", {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    overflowX: "hidden",
    width: theme.spacing(7) + 1,
    [theme.breakpoints.up("sm")]: {
      width: theme.spacing(9) + 1,
    },
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-end",
    padding: theme.spacing(0, 1),
    // necessary for content to be below app bar
    ...theme.mixins.toolbar,
  },
  content: {
    flexGrow: 1,
    padding: theme.spacing(3),
    backgroundColor: "#ffffff",
    color: "#000000",
  },
  toolbarButton: {
    textTransform: "none",
    color: "#ffffff",
    backgroundColor: "inherit",
    "&:hover": {
      backgroundColor: theme.palette.background.light,
    },
  },
}));

export const AppSplash = ({ children }) => {
  const classes = useStyles();
  return (
    <div className={classes.root}>
      <MUIAppBar
        position="fixed"
        className={clsx(classes.appBar, {
          [classes.appBarShift]: false,
        })}
      >
        <Toolbar>
          <Typography variant="h6" noWrap style={{ flexGrow: 1 }}>
            <HCenter>
              <img src={appBarGraphic} alt="CARAVEL" height="40em" />
            </HCenter>
          </Typography>
        </Toolbar>
      </MUIAppBar>
      <main className={classes.content}>
        <div className={classes.toolbar} />
        {children}
      </main>
    </div>
  );
};

const AccountMenu = observer(() => {
  const classes = useStyles();
  const state = useAppState();
  const [anchor, setAnchor] = useState(null);

  const handleClick = (event) => {
    setAnchor(event.currentTarget);
  };

  const handleClose = () => {
    setAnchor(null);
  };

  const handleLogout = () => {
    state.logout();
  };

  return (
    <>
      <Button onClick={handleClick} className={classes.toolbarButton}>
        <AccountCircleIcon />
      </Button>
      <Menu anchorEl={anchor} keepMounted open={!!anchor} onClose={handleClose}>
        <List>
          <ListItem button component={Link} to="/account/profile" key="AccountProfile">
            Profile
          </ListItem>
          <ListItem button onClick={handleLogout} key="AccountLogout">
            Logout
          </ListItem>
        </List>
      </Menu>
    </>
  );
});

export const FallbackAppNavigation = ({ children }) => {
  const classes = useStyles();

  return (
    <div className={classes.root}>
      <MUIAppBar position="fixed" className={clsx(classes.appBar, { [classes.appBarShift]: false })}>
        <Toolbar>
          <Box style={{ flexGrow: 1 }}>
            <img src={appBarGraphic} alt="CARAVEL" width="140em" />
          </Box>
          <Box pl={2}>ERROR</Box>
        </Toolbar>
      </MUIAppBar>
      <main className={classes.content} style={{ width: "100vw" }}>
        <div className={classes.toolbar} />
        <Box>{children}</Box>
      </main>
    </div>
  );
};

const AppNavigationToolbar = observer(() => {
  const classes = useStyles();
  const { user } = useAppState();
  const ds = user.dataStack;
  const branchName = ds === null ? "//" : ds.repo.branch || "<missing>";
  const dataStackName = ds === null ? "//" : ds.config.name || "central";
  return (
    <Toolbar>
      <Box style={{ flexGrow: 1 }}>
        <Link to="/">
          <img src={appBarGraphic} alt="CARAVEL" width="140em" />
        </Link>
      </Box>
      <Box pl={2}>
        <Button variant="text" color="inherit" endIcon={<ArrowDropDownIcon />} className={classes.toolbarButton}>
          stack: {branchName} - project: {dataStackName}
        </Button>
      </Box>
      <Box pl={2}>
        <AccountMenu />
      </Box>
    </Toolbar>
  );
});

const DataNodesIcon = () => <SvgIcon component={DataNodesIconSvg} viewBox="0 0 100 100" />;

export const AppNavigation = observer(({ children }) => {
  const classes = useStyles();
  const theme = useTheme();
  const drawerState = useLocalStorage("diaas:layout.navBarDrawerState", false);

  const loc = useLocation();

  const SectionMenuItem = ({ location, onClick, text, Icon }) => {
    const isCurrentLocation = v.startsWith(loc.pathname, location);
    const style = isCurrentLocation ? { color: theme.palette["primary"].main } : {};
    return (
      <ListItem button component={Link} to={location} key={text} onClick={onClick}>
        <ListItemIcon>
          <Icon style={style} />
        </ListItemIcon>
        <ListItemText primary={text} primaryTypographyProps={{ style: style }} />
      </ListItem>
    );
  };

  return (
    <div className={classes.root}>
      <MUIAppBar position="fixed" className={clsx(classes.appBar, { [classes.appBarShift]: drawerState.v })}>
        <AppNavigationToolbar drawerOpen={drawerState.v} />
      </MUIAppBar>
      <Drawer
        variant="permanent"
        className={clsx(classes.drawer, { [classes.drawerOpen]: drawerState.v, [classes.drawerClose]: !drawerState.v })}
        classes={{ paper: clsx({ [classes.drawerOpen]: drawerState.v, [classes.drawerClose]: !drawerState.v }) }}
      >
        <div className={classes.toolbar}>&nbsp;</div>
        <List>
          <ListItem
            button
            key="openCloseToggle"
            onClick={() => {
              drawerState.v = !drawerState.v;
            }}
          >
            <ListItemIcon>
              <div style={{ transform: drawerState.v ? "scaleX(-1)" : undefined }}>
                <DoubleArrowIcon />
              </div>
            </ListItemIcon>
          </ListItem>
        </List>
        <Divider />
        <List>
          <SectionMenuItem location="/sources" text="Sources" Icon={GetAppIcon} />
          <SectionMenuItem location="/store" text="Storage" Icon={StorageIcon} />
          <SectionMenuItem location="/models" text="Models" Icon={BuildIcon} />
          <SectionMenuItem location="/data-nodes/graph" text="Data Nodes" Icon={DataNodesIcon} />
          <SectionMenuItem
            location="/analytics"
            onClick={() => window.open("/analytics", "caravel-analytics")}
            text="Analytics"
            Icon={SearchIcon}
          />
        </List>
        <Divider />
        <List>
          <SectionMenuItem location="/settings" text="Settings" Icon={SettingsIcon} />
        </List>
      </Drawer>
      <main className={classes.content}>
        <div className={classes.toolbar} />
        <Box>{children}</Box>
      </main>
    </div>
  );
});
