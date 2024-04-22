import "./home.css";
import { html } from "htl";

const TABLE_ICON = () => {
  const x = document.createElement("span");
  x.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-table" viewBox="0 0 16 16"> <path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm15 2h-4v3h4zm0 4h-4v3h4zm0 4h-4v3h3a1 1 0 0 0 1-1zm-5 3v-3H6v3zm-5 0v-3H1v2a1 1 0 0 0 1 1zm-4-4h4V8H1zm0-4h4V4H1zm5-3v3h4V4zm4 4H6v3h4z"/> </svg>`;
  return x;
};
const PIN_ICON = () => {
  const x = document.createElement("span");
  x.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pin-fill" viewBox="0 0 16 16">
  <path fill="#276890" d="M4.146.146A.5.5 0 0 1 4.5 0h7a.5.5 0 0 1 .5.5c0 .68-.342 1.174-.646 1.479-.126.125-.25.224-.354.298v4.431l.078.048c.203.127.476.314.751.555C12.36 7.775 13 8.527 13 9.5a.5.5 0 0 1-.5.5h-4v4.5c0 .276-.224 1.5-.5 1.5s-.5-1.224-.5-1.5V10h-4a.5.5 0 0 1-.5-.5c0-.973.64-1.725 1.17-2.189A6 6 0 0 1 5 6.708V2.277a3 3 0 0 1-.354-.298C4.342 1.674 4 1.179 4 .5a.5.5 0 0 1 .146-.354"/>
</svg>`;
  return x;
};

async function main() {
  const TARGET = document.querySelector("#datasette-pins-homepage-target");
  const data = JSON.parse(document.querySelector("#data")!.textContent!);
  console.log("main", TARGET);
  TARGET?.appendChild(html`
    <div>
      <h2>Pinned Items</h2>

      <div class="datasette-pins-container">
        ${data.map(
          (d) =>
            html`<div class="datasette-pins-item">
              <div>
                <span style="margin-right: .25rem;">${TABLE_ICON()}</span>
                <a href=${`${d.origin_database}/${d.origin_table}`}
                  >${d.origin_database}/${d.origin_table}</a
                >
                <p class="desc"></p>
              </div>
              <div>${PIN_ICON()}</div>
            </div>`
        )}
      </div>
      <div style="text-align: right; font-size: .8rem;">
        <a href="/-/datasette-pins/">Re-order pinned items</a>
      </div>
    </div>
  `);
}
document.addEventListener("DOMContentLoaded", main);
