<<<<<<< HEAD
# IDEKTEP_MHR_APP_REV2
=======
# Nuxt Starter

Look at the [Nuxt documentation](https://nuxt.com/docs/getting-started/introduction) to learn more.

## Setup Frontend
## Node.js and nvm Installation:

```bash
# Download and install npm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# in lieu of restarting the shell
\. "$HOME/.nvm/nvm.sh"

# Download and install Node.js:
nvm install 24

# Verify the Node.js version:
node -v 

# Verify npm version:
npm -v 
```
## Nuxt Installation:
```bash
# Install nuxt with npm
npm create nuxt@latest <project-name>
# change directory into your new project from your terminal:
cd <project-name>
```
## Tailwindcss Installation:
```bash
# Install tailwindcss with npm
npm install tailwindcss @tailwindcss/vite
```

## Setup Backend
## Flask Installation:
```bash
# create venv
python -m venv <project-name>

# Activate venv
source <project-name>/bin/activate

# Install Flask with pip
pip install flask flask-cors
```
## Development Server

Start the development server on `http://localhost:3000`:

```bash
# Install concurrently
npm install -D concurrently
# run
npm run dev:all
```

## Production

Build the application for production:

```bash
# npm
npm run build

# pnpm
pnpm build

# yarn
yarn build

# bun
bun run build
```

Locally preview production build:

```bash
# npm
npm run preview

# pnpm
pnpm preview

# yarn
yarn preview

# bun
bun run preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.
>>>>>>> a35fffc (Init commit)
