import createHttpService from "../services/HttpService";

global.fetch = vi.fn();

describe("createHttpService", () => {
  it("realiza correctamente un POST al crear un jugador", async () => {
    const mockResponse = { id: "1", name: "Juan" };
    fetch.mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const http = createHttpService(); // ✅ ahora sí es función
    const result = await http.createPlayer({ name: "Juan" });

    expect(fetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/players",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ name: "Juan" }),
      })
    );
    expect(result).toEqual(mockResponse);
  });
});
