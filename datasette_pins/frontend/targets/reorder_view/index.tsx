import { html, svg } from "htl";
import Sortable from "sortablejs/modular/sortable.core.esm.js";
import { Api } from "../../api";
import { pinIcon } from "../../components";

const css = `

.list-group-item {
  cursor: grab;
  background-color: white;
  border: 1px solid #454545;
  border-radius: 8px;
  padding: 3px;
  margin-bottom: 6px;
  max-width: min(360px, 100%);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

`;

const DRAG_ICON =
  () => svg`<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" class="bi bi-grip-vertical" viewBox="0 0 16 16">
<path d="M7 2a1 1 0 1 1-2 0 1 1 0 0 1 2 0m3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0M7 5a1 1 0 1 1-2 0 1 1 0 0 1 2 0m3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0M7 8a1 1 0 1 1-2 0 1 1 0 0 1 2 0m3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0m-3 3a1 1 0 1 1-2 0 1 1 0 0 1 2 0m3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0m-3 3a1 1 0 1 1-2 0 1 1 0 0 1 2 0m3 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0"/>
</svg>`;

async function main() {
  const TARGET = document.querySelector("#root")!;
  let sortable: Sortable;
  const status = html`<div style="min-height: 1rem;"></div>`;

  function onSubmit() {
    status.textContent = "Submitting...";
    const newOrder = sortable
      .toArray()
      .map((id: string, order_idx: number) => ({
        id: +id,
        order_idx,
      }));

    Api.reorder(newOrder).then(() => {
      status.textContent = "Re-ordered!";
      setTimeout(() => {
        status.textContent = "";
      }, 750);
    });
  }
  const pins = (await Api.global_pins()).data;

  const page = html`
    <div>
      <h2>Re-order pins</h2>
      <p>Drag+drop pinned items to re-order how they appear on the homepage.</p>
      <div id="items" class="list-group">
        ${pins.map(
          (pin) =>
            html`<div class="list-group-item" data-id=${pin.id.toString()}>
              ${DRAG_ICON()} ${pinIcon(pin)}
              ${pin.origin_database}/${pin.origin_table}
            </div>`
        )}
      </div>
      ${status}
      <style>
        ${css}
      </style>
    </div>
  `;
  TARGET?.appendChild(page);

  sortable = Sortable.create(page.querySelector("#items"), {
    onEnd: onSubmit,
  });
}
document.addEventListener("DOMContentLoaded", main);
