import { Api, GlobalPin } from "../../api";
import "./home.css";
import { html } from "htl";
import { pinIcon, PIN } from "../../components";

function pinUi(pin: GlobalPin, onUnpin) {
  const { id, origin_database, origin_table, metadata } = pin;
  const label = origin_table
    ? `${origin_database}/${origin_table}`
    : origin_database;
  const href = origin_table
    ? `${origin_database}/${origin_table}`
    : origin_database;
  const summary = metadata && metadata.summary ? metadata.summary : "";

  return html`<div
    class="datasette-pins-item"
    onClick=${() => (window.location.href = href)}
  >
    <div class="main">
      <div class="title-bar">
        <div><span>${pinIcon(pin)}</span></div>
        <div class="title-label">
          <a href=${href}>${label}</a>
        </div>
      </div>
      <div>
        <button class="pin-button" onClick=${onUnpin(pin)} data-id=${id}>
          ${PIN()}
        </button>
      </div>
    </div>
    <div><p class="desc">${summary}</p></div>
  </div>`;
}

async function main() {
  const TARGET = document.querySelector("#datasette-pins-homepage-target")!;
  const pins: GlobalPin[] = JSON.parse(
    document.querySelector("#datasette-pins-homepage-data")!.textContent!
  );
  function onUnpin(pin: GlobalPin) {
    return function (e: Event) {
      e.stopPropagation();
      if (
        window.confirm(
          `Are you sure you want to unpin ${pin.origin_database}/${pin.origin_table}?`
        )
      ) {
        Api.unpin(pin.id).then(() => {
          (e.target as HTMLElement).closest(".datasette-pins-item")?.remove();
        });
      }
    };
  }
  TARGET.appendChild(html`
    <div>
      <h2>Pinned Items</h2>
      <div class="datasette-pins-container">
        ${pins.map((pin) => pinUi(pin, onUnpin))}
      </div>
      <div class="reorder">
        <a href="/-/datasette-pins/">Re-order pinned items</a>
      </div>
    </div>
  `);
}
document.addEventListener("DOMContentLoaded", main);
