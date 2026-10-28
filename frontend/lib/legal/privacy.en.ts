import type { LegalDoc } from './types';

export const privacyEn: LegalDoc = {
  title: 'Privacy Policy',
  intro: `Version of {{DATE}}. This policy explains what personal data we collect, why, and how we handle it.`,
  sections: [
    {
      heading: '1. Who we are and what this document covers',
      blocks: [
        { p: `This policy applies to the website sokirdon.com and the Telegram bot @tarott_online_bot (together, the "Service").` },
        { p: `Data controller: {{OPERATOR}} ("we"). Contacts are in section 12.` },
        { p: `The policy applies together with the Terms of Service. We process data in accordance with the personal data protection law of the Republic of Belarus.` },
      ],
    },
    {
      heading: '2. What data we collect',
      blocks: [
        {
          table: {
            head: ['Data', 'What exactly', 'When we receive it'],
            rows: [
              ['Account', 'Telegram ID, name and username in Telegram, language; e-mail if you sign in by e-mail or with Google', 'When you sign in or start the bot'],
              ['Questions and readings', 'The text of your question, the cards and runes drawn, the interpretations received, the date', 'When you do a reading'],
              ['Birth details', 'Date of birth, time and place if you provided them, a name for the natal chart and numerology', 'For the horoscope, natal chart and numerology'],
              ['Payments', 'Telegram Stars payment code, date, amount, activated plan', 'When you pay'],
              ['Activity', 'Daily-visit streak, used limits and credits, invitations', 'While you use the Service'],
              ['Technical data', 'IP address, device and browser type, request times, error records', 'On every request to the Service'],
            ],
          },
        },
        { p: `We do not receive bank card data: payment is made only through Telegram Stars. We receive birth details and a name only when you enter them yourself.` },
      ],
    },
    {
      heading: '3. Why we process it and on what basis',
      blocks: [
        { p: `Basis: your consent, which you give when you accept the Terms and use the Service, and the need to perform the terms, for example to grant Premium you paid for.` },
        { p: `Purposes:` },
        {
          ul: [
            `to show interpretations and keep the history of your readings;`,
            `to count limits, streaks, credits and invitation bonuses;`,
            `to accept payment and deliver what you paid for;`,
            `to send the card of the day and the horoscope if you turned on the mailing;`,
            `to protect the Service from abuse and gaming;`,
            `to answer your requests and improve the Service.`,
          ],
        },
        { p: `Mailing. If you gave a date of birth with the /birthday command or tapped /subscribe, the bot will send the card of the day and the horoscope every morning. You can turn it off at any time with /unsubscribe.` },
        { p: `We do not sell your data and do not use it to advertise other people's products.` },
      ],
    },
    {
      heading: '4. Who receives your data',
      blocks: [
        { p: `Neural network (Anthropic). To obtain an interpretation we send it text. For Tarot and runes that is your question and the cards or runes drawn. For a natal chart it is the name (if you gave one), the date, time and place of birth. For numerology it is the name and date of birth. Your Telegram ID, username and e-mail are not sent to the neural network. Names and details you write in a question do reach it, so write only what you are happy to share.` },
        { p: `Telegram. The bot, sign-in and Telegram Stars payment run through Telegram, under its rules.` },
        { p: `Google. If you sign in with Google, we receive your e-mail and profile name from it.` },
        { p: `Hosting. The server and database run on Railway, the website on Vercel. Your data is stored on their infrastructure.` },
        { p: `By law. We give data to public authorities only on their lawful request.` },
        { p: `We do not pass data to advertising networks or analytics services.` },
      ],
    },
    {
      heading: '5. Transfers abroad',
      blocks: [
        { p: `Our providers (neural network, hosting, Google, Telegram) operate in other countries, including the USA. Your data may therefore be transferred and processed outside the Republic of Belarus. By using the Service you consent to this. We transfer only what the relevant feature needs.` },
      ],
    },
    {
      heading: '6. How long we keep data and how we delete it',
      blocks: [
        { p: `We keep data while you have an account. Questions and readings stay in your history so you can return to them.` },
        { p: `To delete your account, write to us at the contacts in section 12. We will delete the account and its data, or anonymise it, within 30 days. We may keep only what we must keep by law, for example payment records.` },
        { p: `Technical server logs are kept for a limited time determined by the hosting settings. If you block the bot in Telegram we stop writing to you, but the account is not deleted automatically: deletion needs your request.` },
      ],
    },
    {
      heading: '7. Your rights and how to use them',
      blocks: [
        { p: `You have the right to:` },
        {
          ul: [
            `find out what data about you we keep and get a copy;`,
            `correct inaccurate data;`,
            `demand deletion of your data and account;`,
            `withdraw consent to processing (we will then delete the account and the Service will be unavailable where data is needed);`,
            `turn off the mailing with the /unsubscribe command;`,
            `complain to the authority for the protection of data subjects' rights (in Belarus, the National Centre for Personal Data Protection).`,
          ],
        },
        { p: `To use a right, write to us at the contacts in section 12 and give your Telegram ID or account e-mail so we can confirm it is you. We will reply within 15 days.` },
      ],
    },
    {
      heading: '8. How we protect data',
      blocks: [
        { p: `The website and server use a secure connection (HTTPS). Access to the database and the admin panel is restricted. Service keys and passwords are stored separately from the code. User passwords are stored only as hashes.` },
        { p: `No protection is a hundred percent guarantee. If a breach affecting you occurs, we will tell you through the bot or by e-mail.` },
      ],
    },
    {
      heading: '9. Cookies and local storage in your browser',
      blocks: [
        { p: `We use only what the site cannot work without. The cookie NEXT_LOCALE stores the chosen language. Your browser's local storage holds sign-in tokens and your progress, for example the visit streak of signed-out users.` },
        { p: `There are no advertising or analytics cookies, third-party counters or trackers on the site. If you clear the site's data in your browser, you will be signed out.` },
      ],
    },
    {
      heading: '10. Teenagers',
      blocks: [
        { p: `The Service is intended for people aged 16 and over. If you are between 16 and 18, paid features are available only with the consent of a parent or legal guardian. If we learn that data of a person under 16 has reached us, we will delete it. A parent can write to us and we will delete the child's account. If a payment was made without a parent's knowledge, the refund is described in the Terms of Service.` },
      ],
    },
    {
      heading: '11. Changes to this policy',
      blocks: [
        { p: `We publish the new version on the website and announce it in the bot or the channel. The date of the latest update is at the top of the document. If you keep using the Service after a new version is published, you accept it.` },
      ],
    },
    {
      heading: '12. Contacts',
      blocks: [
        { p: `For any question about data, write to: {{CONTACTS}}. Controller: {{OPERATOR}}.` },
      ],
    },
  ],
};
