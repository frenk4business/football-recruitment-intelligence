// Recreate web derivatives without redrawing, recolouring or masking the supplied artwork.
// Sharp is already pinned by Next.js in package-lock.json; this is an offline authoring step.
import sharp from "sharp";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const source = new URL("../brand/source/", import.meta.url);
const output = new URL("../public/brand/", import.meta.url);
await mkdir(output, { recursive: true });
const logo = (name) => sharp(fileURLToPath(new URL(name, source)));

// Remove only the oversized outer canvas. Keep the artwork, original background and clear space.
await logo("Football Recruitment Intelligence Logo(1).png")
  .extract({ left: 192, top: 144, width: 1568, height: 504 })
  .resize(392, 126)
  .webp({ lossless: true })
  .toFile(fileURLToPath(new URL("fri-horizontal.webp", output)));
await logo("Soccer Network Ball Emblem.png")
  .extract({ left: 192, top: 196, width: 864, height: 864 })
  .resize(132, 132)
  .webp({ lossless: true })
  .toFile(fileURLToPath(new URL("fri-emblem.webp", output)));
// The reversed lockup already has its intended dark background. Preserve its complete canvas.
await logo("Football Recruitment Intelligence.png")
  .resize({ width: 1200 })
  .png({ compressionLevel: 9 })
  .toFile(fileURLToPath(new URL("fri-social.png", output)));

// Small display copy of the existing reversed lockup for the dark app sidebar.
await sharp(fileURLToPath(new URL("fri-social.png", output)))
  .resize({ width: 360 })
  .webp({ lossless: true })
  .toFile(fileURLToPath(new URL("fri-sidebar.webp", output)));

const favicon = (size) =>
  logo("Network Soccer Ball Icon.png")
    .extract({ left: 176, top: 184, width: 900, height: 900 })
    .resize(size, size)
    .png({ compressionLevel: 9 })
    .toBuffer();
for (const size of [32, 192]) {
  await writeFile(new URL(`favicon-${size}.png`, output), await favicon(size));
}
await writeFile(new URL("apple-touch-icon.png", output), await favicon(180));

// ICO container with PNG frames for browser/OS choices at 16, 32 and 48 physical pixels.
const sizes = [16, 32, 48];
const frames = await Promise.all(sizes.map(favicon));
const directory = Buffer.alloc(6 + sizes.length * 16);
directory.writeUInt16LE(1, 2);
directory.writeUInt16LE(sizes.length, 4);
let offset = directory.length;
frames.forEach((frame, i) => {
  const entry = 6 + i * 16;
  directory[entry] = sizes[i];
  directory[entry + 1] = sizes[i];
  directory.writeUInt16LE(1, entry + 4);
  directory.writeUInt16LE(32, entry + 6);
  directory.writeUInt32LE(frame.length, entry + 8);
  directory.writeUInt32LE(offset, entry + 12);
  offset += frame.length;
});
await writeFile(
  new URL("../public/favicon.ico", import.meta.url),
  Buffer.concat([directory, ...frames]),
);
console.log("Brand web exports generated from the supplied PNG originals.");
