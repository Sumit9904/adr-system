const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT,
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASSWORD
  }
});

const sendEmail = async ({ to, subject, html }) => {
  try {
    const mailOptions = {
      from: process.env.SMTP_FROM,
      to,
      subject,
      html
    };

    await transporter.sendMail(mailOptions);
    return { success: true };
  } catch (error) {
    console.error('Email sending error:', error);
    return { success: false, error: error.message };
  }
};

const emailTemplates = {
  reportSubmitted: (reportNumber, userName) => ({
    subject: 'ADR Report Submitted Successfully',
    html: `
      <h2>ADR Report Submitted</h2>
      <p>Dear ${userName},</p>
      <p>Your ADR report <strong>${reportNumber}</strong> has been successfully submitted.</p>
      <p>Our team will review your report and you will be notified of any updates.</p>
      <p>Thank you for contributing to drug safety monitoring.</p>
      <br>
      <p>Best regards,<br>ADR Management System</p>
    `
  }),

  reportApproved: (reportNumber, userName) => ({
    subject: 'ADR Report Approved',
    html: `
      <h2>ADR Report Approved</h2>
      <p>Dear ${userName},</p>
      <p>Your ADR report <strong>${reportNumber}</strong> has been approved by our review team.</p>
      <p>The report is now part of our safety database.</p>
      <br>
      <p>Best regards,<br>ADR Management System</p>
    `
  }),

  reportRejected: (reportNumber, userName, reason) => ({
    subject: 'ADR Report Requires Attention',
    html: `
      <h2>ADR Report Status Update</h2>
      <p>Dear ${userName},</p>
      <p>Your ADR report <strong>${reportNumber}</strong> has been reviewed.</p>
      <p><strong>Status:</strong> Rejected</p>
      <p><strong>Reason:</strong> ${reason}</p>
      <p>Please review and submit a new report if necessary.</p>
      <br>
      <p>Best regards,<br>ADR Management System</p>
    `
  }),

  clarificationNeeded: (reportNumber, userName, notes) => ({
    subject: 'Clarification Needed for ADR Report',
    html: `
      <h2>Clarification Required</h2>
      <p>Dear ${userName},</p>
      <p>Your ADR report <strong>${reportNumber}</strong> requires additional information.</p>
      <p><strong>Required Information:</strong></p>
      <p>${notes}</p>
      <p>Please log in to the system and provide the requested details.</p>
      <br>
      <p>Best regards,<br>ADR Management System</p>
    `
  }),

  newUserCreated: (email, tempPassword, fullName) => ({
    subject: 'Welcome to ADR Management System',
    html: `
      <h2>Welcome to ADR Management System</h2>
      <p>Dear ${fullName},</p>
      <p>Your account has been created successfully.</p>
      <p><strong>Login Credentials:</strong></p>
      <p>Email: ${email}<br>
      Temporary Password: ${tempPassword}</p>
      <p>Please log in and change your password immediately.</p>
      <p>Login URL: ${process.env.FRONTEND_URL}/login</p>
      <br>
      <p>Best regards,<br>ADR Management System</p>
    `
  })
};

module.exports = { sendEmail, emailTemplates };
