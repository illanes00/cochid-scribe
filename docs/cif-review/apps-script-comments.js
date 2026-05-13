/**
 * CIF-EP Medicamentos — Insertar comentarios de revisión
 *
 * INSTRUCCIONES:
 * 1. Abrir el documento en Google Docs
 * 2. Extensiones → Apps Script
 * 3. Pegar este código (reemplazar todo lo que haya)
 * 4. En el menú izquierdo de Apps Script: Servicios (+) → Drive API → Agregar
 * 5. Click en "Ejecutar" (▶) en la función testComments
 * 6. Autorizar cuando lo pida
 * 7. Verificar que los comentarios se ven anclados en el doc
 * 8. Si funciona, cambiar TEST_MODE = false y ejecutar insertAllComments
 */

const TEST_MODE = true;
const DOC_ID = '1mp7jKTfrLQ478bBPNGX60hwerI_xakIFBsqHSrO-Lbg';

function testComments() {
  // Test con solo 2 comentarios para verificar que el anchoring funciona
  const testComments = [
    {
      id: 'C1',
      author: 'CIF (Francisca Rodríguez)',
      source: 'Email 18/3/2026',
      content: 'La tabla de coberturas generales no incorpora DAC, pese a que este instrumento formaba parte de los componentes que se solicitó considerar.',
      searchText: 'Matriz de coberturas'
    },
    {
      id: 'C2',
      author: 'Eduardo Undurraga (Director)',
      source: 'Email 30/3/2026',
      content: 'Sería mucho menos prescriptivo en el informe. EP no puede jugarse en una solución sino que nuestro rol es mostrar evidencia y datos.',
      searchText: 'Seguro Universal con tope'
    }
  ];

  insertCommentsBatch(testComments);
}

function insertCommentsBatch(commentsList) {
  const doc = DocumentApp.openById(DOC_ID);
  const body = doc.getBody();

  let success = 0;
  let failed = 0;

  for (const c of commentsList) {
    try {
      // Find the target text in the document
      const searchResult = body.findText(c.searchText);

      if (searchResult) {
        const element = searchResult.getElement();
        const text = element.asText().getText();
        const start = searchResult.getStartOffset();
        const end = searchResult.getEndOffsetInclusive();
        const quotedText = text.substring(start, end + 1);

        // Format comment text
        const commentText = `[${c.id}] ${c.author} — ${c.source}\n\n${c.content}`;

        // Try Drive API v2 with context (might anchor properly)
        const comment = {
          content: commentText,
          context: {
            type: 'text/html',
            value: quotedText
          }
        };

        Drive.Comments.insert(comment, DOC_ID);
        success++;
        Logger.log(`✅ ${c.id}: anchored to "${quotedText.substring(0, 40)}..."`);
      } else {
        // Fallback: create without context
        Logger.log(`⚠️ ${c.id}: text "${c.searchText}" not found, creating unanchored`);
        Drive.Comments.insert({content: `[${c.id}] ${c.author} — ${c.source}\n\n${c.content}`}, DOC_ID);
        failed++;
      }
    } catch (e) {
      Logger.log(`❌ ${c.id}: ${e.message}`);
      failed++;
    }
  }

  Logger.log(`\nDone: ${success} anchored, ${failed} failed/unanchored`);
}
