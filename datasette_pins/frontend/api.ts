async function api(path: string, params?: { method?: string; data?: any }) {
  const { method, data } = params ?? {};
  // TODO base_url
  return fetch(`${path}`, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: data ? JSON.stringify(data) : undefined,
  }).then((response) => response.json());
}

export interface GlobalPin {
  id: number;
  pinned_actor_id: string;
  pin_location: "home";
  item_type: "database" | "table";
  origin_database: string;
  origin_table: string;
  order_idx: number;
  identifier: string | null;
}
export class Api {
  static async reorder(new_order: { id: number; order_idx: number }[]) {
    return api("/-/datasette-pins/api/reorder", {
      method: "POST",
      data: {
        new_order: new_order,
      },
    });
  }
  static async global_pins(): Promise<{ data: GlobalPin[] }> {
    return api("/-/datasette-pins/api/global_pins");
  }
}
