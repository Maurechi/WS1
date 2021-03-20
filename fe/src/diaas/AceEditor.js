// NOTE this is a disaster. eslint wants to reoder import
// alphabetically (which is somthing we generally want in this code
// base). however AceEditor needs to be loaded before its dependencies
// (and this is really AceEditor's fault). So we have to just ignore
// eslint in this file.  20201215:mb
/* eslint-disable */

import AceEditor from "react-ace";

import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/mode-sql";
import "ace-builds/src-noconflict/theme-solarized_light";

export default AceEditor;
