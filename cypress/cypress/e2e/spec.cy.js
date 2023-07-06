describe('My First Test', () => {
  it('Visits my Personal Website', () => {
    cy.visit('https://davidkayode.com')

    cy.request({
      url: 'https://cu2jqacorb.execute-api.us-east-1.amazonaws.com/default/visitorCounterLambda',
      method: 'POST',
    })

    .should((response) => {
      console.log(JSON.parse(response.body).value)
      expect(response.status).to.eq(200)
      expect(response.body).length.to.be.greaterThan(1)
      expect(JSON.parse(response.body).value).to.be.greaterThan(1)
    });
  })
})