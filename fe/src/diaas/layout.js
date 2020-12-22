import {
  AppBar as MUIAppBar,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Menu,
  Toolbar,
  Typography,
} from "@material-ui/core";
import { makeStyles, useTheme } from "@material-ui/core/styles";
import AccountCircleIcon from "@material-ui/icons/AccountCircle";
import BuildIcon from "@material-ui/icons/Build";
import ChevronLeftIcon from "@material-ui/icons/ChevronLeft";
import ChevronRightIcon from "@material-ui/icons/ChevronRight";
import CollectionsBookmarkIcon from "@material-ui/icons/CollectionsBookmark";
import GetAppIcon from "@material-ui/icons/GetApp";
import InfoIcon from "@material-ui/icons/Info";
import MenuIcon from "@material-ui/icons/Menu";
import MenuBookIcon from "@material-ui/icons/MenuBook";
import PlayArrowIcon from "@material-ui/icons/PlayArrow";
import SearchIcon from "@material-ui/icons/Search";
import SettingsIcon from "@material-ui/icons/Settings";
import clsx from "clsx";
import { observer } from "mobx-react-lite";
import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import v from "voca";

import { useAppState } from "diaas/state";

export const HCenter = ({ children, ...BoxProps }) => (
  <Box display="flex" width="100%" justifyContent="center" {...BoxProps}>
    {children}
  </Box>
);

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
  },
  appBarShift: {
    marginLeft: drawerWidth,
    width: `calc(100% - ${drawerWidth}px)`,
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
          <Typography variant="h6" noWrap>
            Caravel
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
      <Button variant="contained" color="primary" onClick={handleClick}>
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

const AppNavigationToolbar = observer(({ drawerOpen, handleDrawerOpen }) => {
  const state = useAppState();
  const classes = useStyles();
  return (
    <Toolbar>
      <IconButton
        color="inherit"
        aria-label="open drawer"
        onClick={handleDrawerOpen}
        edge="start"
        className={clsx(classes.menuButton, {
          [classes.hide]: drawerOpen,
        })}
      >
        <MenuIcon />
      </IconButton>
      <Typography variant="h6" noWrap style={{ flexGrow: 1 }}>
        <Link to="/" style={{ color: "inherit", textDecoration: "none" }}>
          Caravel
        </Link>
      </Typography>
      <Button variant="contained" color="primary">
        Branch: {state.user.dataStacks.length > 0 ? state.user.dataStacks[0].branch : '---'}
      </Button>
      <Button variant="contained" color="primary">
        Data Stack: {state.user.dataStacks.length > 0 ? state.user.dataStacks[0].name : '---'}
      </Button>
      <AccountMenu />
    </Toolbar>
  );
});

export const AppNavigation = ({ children }) => {
  const classes = useStyles();
  const theme = useTheme();
  const [open, setOpen] = React.useState(false);

  const handleDrawerOpen = () => {
    setOpen(true);
  };

  const handleDrawerClose = () => {
    setOpen(false);
  };

  const loc = useLocation();
  const typeographyOnLocation = (prefix) => ({
    color: v.startsWith(loc.pathname, prefix) ? "secondary" : "primary",
  });

  return (
    <div className={classes.root}>
      <MUIAppBar
        position="fixed"
        className={clsx(classes.appBar, {
          [classes.appBarShift]: open,
        })}
      >
        <AppNavigationToolbar handleDrawerOpen={handleDrawerOpen} drawerOpen={open} />
      </MUIAppBar>
      <Drawer
        variant="permanent"
        className={clsx(classes.drawer, {
          [classes.drawerOpen]: open,
          [classes.drawerClose]: !open,
        })}
        classes={{
          paper: clsx({
            [classes.drawerOpen]: open,
            [classes.drawerClose]: !open,
          }),
        }}
      >
        <div className={classes.toolbar}>
          <IconButton onClick={handleDrawerClose}>
            {theme.direction === "rtl" ? <ChevronRightIcon /> : <ChevronLeftIcon />}
          </IconButton>
        </div>
        <Divider />
        <List>
          <ListItem button component={Link} to="/modules/" key="Modules">
            <ListItemIcon>
              <CollectionsBookmarkIcon />
            </ListItemIcon>
            <ListItemText primary="Modules" primaryTypographyProps={typeographyOnLocation("/modules")} />
          </ListItem>
        </List>
        <Divider />
        <List>
          <ListItem button component={Link} to="/sources/" key="Sources">
            <ListItemIcon>
              <GetAppIcon />
            </ListItemIcon>
            <ListItemText primary="Sources" primaryTypographyProps={typeographyOnLocation("/sources")} />
          </ListItem>
          <ListItem button component={Link} to="/workbench/" key="Workbench">
            <ListItemIcon>
              <BuildIcon />
            </ListItemIcon>
            <ListItemText primary="Workbench" primaryTypographyProps={typeographyOnLocation("/workbench")} />
          </ListItem>
          <ListItem button component={Link} to="/jobs/" key="Jobs">
            <ListItemIcon>
              <PlayArrowIcon />
            </ListItemIcon>
            <ListItemText primary="Jobs" primaryTypographyProps={typeographyOnLocation("/jobs")} />
          </ListItem>
          <ListItem button component={Link} to="/analytics/" key="Analytics">
            <ListItemIcon>
              <SearchIcon />
            </ListItemIcon>
            <ListItemText primary="Analytics" primaryTypographyProps={typeographyOnLocation("/analytics")} />
          </ListItem>
        </List>
        <Divider />
        <List>
          <ListItem button component={Link} key="Catalog" to="/catalog/">
            <ListItemIcon>
              <MenuBookIcon />
            </ListItemIcon>
            <ListItemText primary="Catalog" />
          </ListItem>
          <ListItem button component={Link} to="/monitoring/" key="Monitoring">
            <ListItemIcon>
              <InfoIcon />
            </ListItemIcon>
            <ListItemText primary="Monitoring" />
          </ListItem>
          <ListItem button component={Link} to="/settings/" key="Settings">
            <ListItemIcon>
              <SettingsIcon />
            </ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItem>
        </List>
      </Drawer>
      <main className={classes.content}>
        <div className={classes.toolbar} />
        <Box p={4}>{children}</Box>
      </main>
    </div>
  );
};
