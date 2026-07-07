FROM node:22-bookworm

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
RUN node -e "
  const {execSync} = require('child_process');
  const targets = ['lightningcss', '@tailwindcss/oxide', 'unrs-resolver'];
  const toInstall = targets.map(p => {
    try {
      const pkg = require('./node_modules/' + p + '/package.json');
      const linux = Object.keys(pkg.optionalDependencies || {})
        .find(n => n.includes('linux-x64-gnu'));
      return linux ? linux + '@' + pkg.version : null;
    } catch(e) { return null; }
  }).filter(Boolean).join(' ');
  if (toInstall) {
    console.log('Installing missing:', toInstall);
    execSync('npm install --no-save ' + toInstall, {stdio:'inherit'});
  }
"
COPY . .

ENV NODE_ENV=production
RUN npm run build -- --webpack

EXPOSE 3000
CMD ["npm", "start"]
