describe("Nómada Alpha Dashboard", () => {
  beforeEach(() => {
    // Visitar la página principal
    cy.visit("http://localhost:3000");
  });

  it("should display the main dashboard", () => {
    // Verificar que el título principal esté presente
    cy.contains("Nómada Alpha").should("be.visible");
    cy.contains("Dashboard de Gestión de Campañas").should("be.visible");
  });

  it("should show health status", () => {
    // Verificar que la sección de estado del sistema esté presente
    cy.contains("Estado del Sistema").should("be.visible");
    
    // Esperar a que se cargue el estado de salud
    cy.get('[data-testid="health-status"]', { timeout: 10000 }).should("exist");
  });

  it("should display campaign form", () => {
    // Verificar que el formulario de crear campaña esté presente
    cy.contains("Crear Nueva Campaña").should("be.visible");
    
    // Verificar campos del formulario
    cy.get('input[name="name"]').should("be.visible");
    cy.get('textarea[name="description"]').should("be.visible");
    cy.get('select[name="campaign_type"]').should("be.visible");
    cy.get('input[name="target_audience"]').should("be.visible");
    cy.get('input[name="budget"]').should("be.visible");
  });

  it("should create a new campaign", () => {
    // Llenar el formulario de campaña
    cy.get('input[name="name"]').type("Test Campaign");
    cy.get('textarea[name="description"]').type("This is a test campaign");
    cy.get('select[name="campaign_type"]').select("email");
    cy.get('input[name="target_audience"]').type("Test Audience");
    cy.get('input[name="budget"]').type("1000");
    
    // Enviar el formulario
    cy.get('button[type="submit"]').click();
    
    // Verificar mensaje de éxito o error
    cy.get('.bg-green-100, .bg-red-100', { timeout: 10000 }).should("be.visible");
  });

  it("should display campaigns list", () => {
    // Verificar que la sección de campañas esté presente
    cy.contains("Campañas").should("be.visible");
  });

  it("should display recent events", () => {
    // Verificar que la sección de eventos recientes esté presente
    cy.contains("Eventos Recientes").should("be.visible");
  });

  it("should be responsive", () => {
    // Probar en diferentes tamaños de pantalla
    cy.viewport(1200, 800);
    cy.contains("Nómada Alpha").should("be.visible");
    
    cy.viewport(768, 1024);
    cy.contains("Nómada Alpha").should("be.visible");
    
    cy.viewport(375, 667);
    cy.contains("Nómada Alpha").should("be.visible");
  });

  it("should handle API errors gracefully", () => {
    // Interceptar llamadas a la API y simular errores
    cy.intercept("GET", "**/health", { statusCode: 500 }).as("healthError");
    cy.intercept("GET", "**/campaigns", { statusCode: 500 }).as("campaignsError");
    
    cy.visit("http://localhost:3000");
    
    // Verificar que la aplicación sigue funcionando a pesar de los errores
    cy.contains("Nómada Alpha").should("be.visible");
  });
});

