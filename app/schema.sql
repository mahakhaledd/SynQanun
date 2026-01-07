-- Always target dbo schema
IF OBJECT_ID('dbo.Judgment_Principle', 'U') IS NOT NULL DROP TABLE dbo.Judgment_Principle;
IF OBJECT_ID('dbo.Fatwa_Principle', 'U') IS NOT NULL DROP TABLE dbo.Fatwa_Principle;
IF OBJECT_ID('dbo.Law_Article', 'U') IS NOT NULL DROP TABLE dbo.Law_Article;
IF OBJECT_ID('dbo.Judgment', 'U') IS NOT NULL DROP TABLE dbo.Judgment;
IF OBJECT_ID('dbo.Fatwa', 'U') IS NOT NULL DROP TABLE dbo.Fatwa;
IF OBJECT_ID('dbo.Law', 'U') IS NOT NULL DROP TABLE dbo.Law;

CREATE TABLE dbo.Law (
    law_id INT IDENTITY(1,1) PRIMARY KEY,
    law_year INT NOT NULL,
    issue_date DATE NULL,
    publication_date DATE NULL,
    effective_date DATE NULL,
    title NVARCHAR(MAX) NOT NULL,
    gazette_reference NVARCHAR(MAX) NULL
);

CREATE TABLE dbo.Law_Article (
    id INT IDENTITY(1,1) PRIMARY KEY,
    law_id INT NOT NULL,

    article_number NVARCHAR(50) NOT NULL,
    article_type NVARCHAR(20) NOT NULL,
    is_repeated BIT NOT NULL CONSTRAINT DF_LawArticle_IsRepeated DEFAULT 0,

    original_text NVARCHAR(MAX) NULL,
    final_text NVARCHAR(MAX) NULL,
    final_text_date DATE NULL,

    CONSTRAINT FK_Law_Article_Law
        FOREIGN KEY (law_id)
        REFERENCES dbo.Law(law_id)
        ON DELETE CASCADE,

    CONSTRAINT CHK_LawArticle_Type
        CHECK (article_type IN (N'issuance', N'content')),

    CONSTRAINT UQ_Law_Article
        UNIQUE (law_id, article_number, article_type)
);

CREATE TABLE dbo.Fatwa (
    fatwa_id INT IDENTITY(1,1) PRIMARY KEY,
    fatwa_number INT NULL,
    fatwa_year INT NULL,
    issued_date DATE NULL,
    session_date DATE NULL,
    subject NVARCHAR(MAX) NULL,
    authority NVARCHAR(MAX) NULL,
    full_text NVARCHAR(MAX) NULL,
    file_number NVARCHAR(50) NULL,
    facts NVARCHAR(MAX) NULL,
    application NVARCHAR(MAX) NULL,
    opinion NVARCHAR(MAX) NULL
);

CREATE TABLE dbo.Fatwa_Principle (
    principle_id INT IDENTITY(1,1) PRIMARY KEY,
    fatwa_id INT NOT NULL,

    principle_number INT NULL,
    principle_text NVARCHAR(MAX) NULL,

    CONSTRAINT FK_Fatwa_Principle_Fatwa
        FOREIGN KEY (fatwa_id)
        REFERENCES dbo.Fatwa(fatwa_id)
        ON DELETE CASCADE
);

CREATE TABLE dbo.Judgment (
    judgment_id INT IDENTITY(1,1) PRIMARY KEY,
    court_name NVARCHAR(MAX) NULL,
    case_type NVARCHAR(50) NULL,
    appeal_number INT NULL,
    judicial_year INT NULL,
    session_date DATE NULL,

    technical_office_number NVARCHAR(50) NULL,
    volume_number NVARCHAR(50) NULL,
    page_number NVARCHAR(50) NULL,
    rule_number NVARCHAR(50) NULL,
    reference_number NVARCHAR(50) NULL,

    judicial_panel NVARCHAR(MAX) NULL,
    facts NVARCHAR(MAX) NULL,
    reasons NVARCHAR(MAX) NULL
);

CREATE TABLE dbo.Judgment_Principle (
    principle_id INT IDENTITY(1,1) PRIMARY KEY,
    judgment_id INT NOT NULL,

    principle_number INT NULL,
    principle_text NVARCHAR(MAX) NULL,

    CONSTRAINT FK_Judgment_Principle_Judgment
        FOREIGN KEY (judgment_id)
        REFERENCES dbo.Judgment(judgment_id)
        ON DELETE CASCADE
);

-- Helpful indexes for idempotent loaders
CREATE UNIQUE INDEX UX_Judgment_ReferenceNumber
ON dbo.Judgment(reference_number)
WHERE reference_number IS NOT NULL;

CREATE UNIQUE INDEX UX_Judgment_FallbackKey
ON dbo.Judgment(appeal_number, judicial_year, session_date)
WHERE appeal_number IS NOT NULL AND judicial_year IS NOT NULL AND session_date IS NOT NULL;

CREATE UNIQUE INDEX UX_Fatwa_NumberYear
ON dbo.Fatwa(fatwa_number, fatwa_year)
WHERE fatwa_number IS NOT NULL AND fatwa_year IS NOT NULL;
