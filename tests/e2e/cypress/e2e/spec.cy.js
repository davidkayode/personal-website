const hosts = ['https://davidkayode.com', 'https://www.davidkayode.com'];

describe('Live site', () => {
  hosts.forEach((host) => {
    it(`shows a visitor count on ${host}`, () => {
      cy.visit(host);
      cy.get('.counter', { timeout: 15000 }).invoke('text').should('match', /^\d+$/);
    });
  });

  ['/assets/headshot.jpg', '/assets/David_Kayode_Resume.pdf'].forEach((path) => {
    it(`serves ${path}`, () => {
      cy.request(`https://davidkayode.com${path}`).its('status').should('eq', 200);
    });
  });

  it('publishes the counter API in /config.json', () => {
    cy.request('https://davidkayode.com/config.json').its('body.counterApiUrl').should('match', /^https:\/\/.+\/prod\/count$/);
  });
});
