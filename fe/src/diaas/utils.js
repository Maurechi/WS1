export const logIt = (...args) => {
  let lastValue = null;
  for (let i = 0; i < args.length; i++) {
    lastValue = args[i];
  }
  console.log.apply(console, args);
  return lastValue;
};
