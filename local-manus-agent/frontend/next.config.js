/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable static export for Tauri desktop builds
  // In web mode, this still works normally with `next dev`
  output: process.env.TAURI_BUILD ? "export" : undefined,
  experimental: {
    // Android/Termux does not have a supported native next-swc binary,
    // so force the wasm backend there.
    useWasmBinary: process.platform === "android",
  },
};

module.exports = nextConfig;
