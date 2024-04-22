import { html } from "htl";
import Sortable from "sortablejs/modular/sortable.core.esm.js";
import { Api } from "../../api";

async function main() {
  const TARGET = document.querySelector("#root");
  let sortable: Sortable;
  let itemsElement: HTMLElement;
  function onSubmit() {
    const newOrder = sortable.toArray().map((id, order_idx) => ({
      id: +id,
      order_idx,
    }));

    Api.reorder(newOrder);
  }
  const pins = (await Api.global_pins()).data;
  console.log(pins);
  const page = TARGET?.appendChild(html`
    <div>
      <div id="items" class="list-group">
        ${pins.map(
          (pin) =>
            html`<div class="list-group-item" data-id=${pin.id.toString()}>
              ${pin.origin_database}/${pin.origin_table}
            </div>`
        )}
      </div>
      <button onClick=${onSubmit}>Submit</button>
    </div>
  `);
  console.log(page.querySelector("#items").children.length);
  sortable = Sortable.create(page.querySelector("#items"));
}
document.addEventListener("DOMContentLoaded", main);
