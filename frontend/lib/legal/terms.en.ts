import type { LegalDoc } from './types';

export const termsEn: LegalDoc = {
  title: 'Terms of Service',
  intro: `Version of {{DATE}}. These terms set the rules for using Tarot Online: the website sokirdon.com and the Telegram bot @tarott_online_bot (together, the "Service").`,
  sections: [
    {
      heading: '1. General',
      blocks: [
        { p: `1.1. The Service is operated by {{OPERATOR}} ("we"). You can reach us at the contacts in section 12.` },
        { p: `1.2. You accept these terms when you create an account, start the bot or begin using the website. If you do not agree, do not use the Service.` },
        { p: `1.3. These terms apply together with the Privacy Policy (section 9) and the rules of individual promotions and contests (section 7).` },
      ],
    },
    {
      heading: '2. What the Service does',
      blocks: [
        { p: `2.1. The Service offers Tarot and rune readings, a natal chart, numerology, a horoscope, a card of the day, the history of your readings and daily-visit streaks.` },
        { p: `2.2. Interpretations are written by a neural network (Claude models from Anthropic) based on the cards drawn and your question. Cards and runes are drawn at random.` },
        { p: `2.3. Some features are free; others require a Premium subscription or credits (section 6). We may change the features and limits. Current terms are shown in the Service.` },
        { p: `2.4. We try to keep the Service running without interruptions but do not guarantee it. Outages, updates and downtime happen for reasons outside our control.` },
      ],
    },
    {
      heading: '3. Account and age',
      blocks: [
        { p: `3.1. You can sign in with Telegram, Google or e-mail. The bot needs your Telegram account. Some features work without signing in, with a daily limit.` },
        { p: `3.2. The Service is intended for people aged 16 and over. We do not check age with documents. By using the Service you confirm that you are at least 16. If you are between 16 and 18, paid features are available only with the consent of a parent or legal guardian. If a payment was made without their knowledge, write to us and we will refund it.` },
        { p: `3.3. You are responsible for access to your account and for everything done in it. If you suspect someone else is using your account, tell us.` },
        { p: `3.4. One person, one account. Additional accounts created to collect bonuses are not allowed (section 7).` },
      ],
    },
    {
      heading: '4. Rules of use',
      blocks: [
        { p: `4.1. You must not:` },
        {
          ul: [
            `get around limits, payment or other restrictions of the Service;`,
            `create several accounts for bonuses, invitations or contests;`,
            `automate requests (bots, scripts) or overload the Service;`,
            `share Premium access with other people or resell it;`,
            `copy the Service's texts and images in bulk;`,
            `try to hack the Service or obtain other people's data;`,
            `write threats, insults or illegal content in your questions.`,
          ],
        },
        { p: `4.2. If you break the rules, we may restrict features, revoke bonuses and close your account. In case of a serious violation, payment for the period of the violation is not refunded.` },
      ],
    },
    {
      heading: '5. What interpretations are and are not',
      blocks: [
        { p: `5.1. Readings and interpretations are entertainment and a way to look at your situation from another angle. They are not a forecast of the future and not a prediction of events.` },
        { p: `5.2. The neural network can make mistakes, oversimplify and invent details. An interpretation must not be treated as fact about the people and circumstances you ask about.` },
        { p: `5.3. The Service does not provide medical, legal, financial or psychological advice. Decisions about health, money, work, relationships and safety are yours, with a specialist's help where needed.` },
        { p: `5.4. If you are struggling or thinking about harming yourself or others, contact a specialist or the emergency services (in Belarus: 112). The Service is not a substitute for help.` },
        { p: `5.5. Your questions are processed by a third-party neural network provider. Do not write passport details, card numbers, passwords or other information that must not reach third parties.` },
        { p: `5.6. On the topics of money, health and law the Service does not give advice, verdicts or predictions of outcomes. Answers to such questions describe the mood of the spread and contain questions to reflect on.` },
      ],
    },
    {
      heading: '6. Paid features: Premium and credits',
      blocks: [
        { p: `6.1. Premium gives access to extended features for the paid period (currently 30 days). Credits are separate one-off readings on top of the free ones. The price and contents are shown in the Service at the time of purchase.` },
        { p: `6.2. Payment is made with Telegram Stars in the bot. Telegram processes the payment; we do not receive or store payment details.` },
        { p: `6.3. After a successful payment, Premium and credits are granted automatically, usually immediately. If that did not happen, write to us with the payment code. We will check the payment and grant what you paid for manually.` },
        { p: `6.4. A Telegram Stars payment covers one paid period and does not renew by itself. To extend Premium, pay for it again.` },
        { p: `6.5. Refunds. If what you paid for was not delivered or did not work through the Service's fault, we will refund the money or extend the period, at your choice. Contact us within 30 days of the payment date. If the service has already been provided (Premium activated, credits granted) and works, the money is not refunded. The rights that consumer protection law gives you are not limited by this clause.` },
        { p: `6.6. We may change prices. A change does not affect a period you have already paid for.` },
      ],
    },
    {
      heading: '7. Free readings, invitations and contests',
      blocks: [
        { p: `7.1. A limited number of readings is free each day (currently 3). The limit resets daily; unused readings do not accumulate. We may change the limit.` },
        { p: `7.2. Inviting a friend. The /invite command in the bot gives you a personal link. When a person who has not used the bot before makes their first reading, you both receive 3 credits. The reward is paid for no more than 5 invited people.` },
        { p: `7.3. Bonus credits cannot be exchanged for money or given to another person. They do not replace paid Premium and are not refunded in money.` },
        { p: `7.4. We may withhold or revoke bonuses if we see abuse: fake accounts, inviting yourself, automation, several accounts of one person.` },
        { p: `7.5. Contests run under separate rules published in the channel or the bot. If they conflict with these terms, the contest's rules apply to the contest. Prizes (for example, Premium) cannot be exchanged for money.` },
        { p: `7.6. We may change or end promotions and the bonus programme. Bonuses already granted do not expire without reason, except in the case of clause 7.4.` },
      ],
    },
    {
      heading: '8. Intellectual property',
      blocks: [
        { p: `8.1. The texts, design, source code and images of the Service, and its name, belong to us or are used with the permission of rights holders.` },
        { p: `8.2. You receive a personal, non-commercial right to use the Service and its materials. You may not copy or resell the Service's materials, or use them to train neural networks, without our written consent.` },
        { p: `8.3. Your questions remain yours. You allow us to store them, send them to the neural network to obtain an interpretation, and show them to you in your reading history. We do not publish your questions and results without your consent.` },
        { p: `8.4. You may use a received interpretation for personal purposes and share it, naming the source. We do not guarantee the text is unique: similar questions and cards can produce similar answers.` },
      ],
    },
    {
      heading: '9. Personal data',
      blocks: [
        { p: `9.1. To run the Service we process: account data (Telegram ID, name and username, e-mail if you sign in by e-mail or with Google), your date of birth, time and place if you provided them, your questions, the cards and runes drawn and the interpretations received, payment records (without a card number), and technical data about visits.` },
        { p: `9.2. Why: to show interpretations, count limits and streaks, grant bonuses, accept payment, send the card of the day and the horoscope (if you turned on the mailing) and improve the Service.` },
        { p: `9.3. Who receives it: the neural network (Anthropic, USA), Telegram (payments and sign-in), hosting providers (Railway, Vercel) and Google (sign-in). We send the neural network only what the interpretation needs: your question and the cards drawn, and for a natal chart the name, date, time and place of birth, and for numerology the name and date of birth. Data may be processed outside Belarus.` },
        { p: `9.4. We keep data while you have an account. On your request we will delete or anonymise it, except what we must keep by law (for example, payment records).` },
        { p: `9.5. Your rights and how to exercise them are described in the Privacy Policy (the /privacy page), in accordance with the data protection law of the Republic of Belarus.` },
      ],
    },
    {
      heading: '10. Liability',
      blocks: [
        { p: `10.1. The Service is provided "as is". We do not guarantee that it will run without errors or interruptions, or that interpretations will be accurate, useful or suitable for your purpose.` },
        { p: `10.2. We are not responsible for decisions you make based on interpretations, or for losses resulting from them.` },
        { p: `10.3. Our liability to you is limited to actual damage and does not exceed the amount you paid the Service in the last 3 months, to the extent the law allows. This does not limit rights that consumer protection law does not allow to be limited.` },
        { p: `10.4. We are not responsible for failures of third parties: Telegram, payment systems, hosting, the neural network and internet providers.` },
      ],
    },
    {
      heading: '11. Changes and ending access',
      blocks: [
        { p: `11.1. We may change these terms. We publish the new version on the website and announce it in the bot or the channel. If you keep using the Service after the new version takes effect, you accept it. If you do not agree, stop using it. Changes to prices and paid terms do not affect a period you have already paid for.` },
        { p: `11.2. You may stop using the Service and ask us to delete your account at any time. The paid Premium period is not refunded in that case, except under clause 6.5.` },
        { p: `11.3. We may suspend or close access for a violation of the terms (section 4) and where the law requires. If we shut the Service down entirely, we will warn you in advance and refund the unused part of a Premium period.` },
      ],
    },
    {
      heading: '12. Law, disputes and contacts',
      blocks: [
        { p: `12.1. These terms are governed by the law of the Republic of Belarus.` },
        { p: `12.2. We will first try to settle a dispute by negotiation. Write to us at the contacts below and we will reply within 14 days. If we cannot agree, the dispute is heard in court in accordance with the law of the Republic of Belarus.` },
        { p: `12.3. If any clause turns out to be invalid, the others remain in force.` },
        { p: `12.4. Contacts: {{CONTACTS}}. Operator of the Service: {{OPERATOR}}.` },
      ],
    },
  ],
};
