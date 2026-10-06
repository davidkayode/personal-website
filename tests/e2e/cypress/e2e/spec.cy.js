// Runs after every deploy. It must never add a real visit: page loads use a
// stubbed counter POST, and the live API is checked through read-only /health.
const hosts = ['https://davidkayode.com', 'https://www.davidkayode.com'];

describe('Live site', () => {
  hosts.forEach((host) => {
    it(`wires the visitor count into the footer on ${host}`, () => {
      cy.intercept('POST', '**/prod/count', { statusCode: 200, body: { value: 123 } }).as('count');
      cy.visit(host);
      cy.wait('@count');
      cy.get('.counter', { timeout: 15000 }).should('have.text', '123');
    });
  });

  it('reports a healthy counter API without counting a visit', () => {
    cy.request('https://davidkayode.com/config.json').its('body.counterApiUrl').then((url) => {
      expect(url).to.match(/^https:\/\/.+\/prod\/count$/);
      cy.request(url.replace(/\/count$/, '/health')).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body.status).to.eq('ok');
        expect(response.body.value).to.be.a('number');
      });
    });
  });

  ['/assets/headshot.jpg', '/assets/David_Kayode_Resume.pdf'].forEach((path) => {
    it(`serves ${path}`, () => {
      cy.request(`https://davidkayode.com${path}`).its('status').should('eq', 200);
    });
  });
});
