<?php

namespace DoctrineMigrations;

use Doctrine\DBAL\Migrations\AbstractMigration;
use Doctrine\DBAL\Schema\Schema;

/**
 * Auto-generated Migration: Please modify to your needs!
 */
class Version20181029110359 extends AbstractMigration
{
    /**
     * @param Schema $schema
     */
    public function up(Schema $schema)
    {
        // this up() migration is auto-generated, please modify it to your needs
        $this->abortIf($this->connection->getDatabasePlatform()->getName() !== 'mysql', 'Migration can only be executed safely on \'mysql\'.');

        $this->addSql('CREATE TABLE commit (id INT AUTO_INCREMENT NOT NULL, ref VARCHAR(64) NOT NULL, branch VARCHAR(100) NOT NULL, message LONGTEXT NOT NULL, status VARCHAR(20) NOT NULL, PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE queue_dependency (id INT AUTO_INCREMENT NOT NULL, queue_item_id INT NOT NULL, requirement_id INT NOT NULL, INDEX IDX_90AE2CA0F0EDC960 (queue_item_id), INDEX IDX_90AE2CA07B576F77 (requirement_id), PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE = InnoDB');
        $this->addSql('ALTER TABLE queue_dependency ADD CONSTRAINT FK_90AE2CA0F0EDC960 FOREIGN KEY (queue_item_id) REFERENCES queue (id)');
        $this->addSql('ALTER TABLE queue_dependency ADD CONSTRAINT FK_90AE2CA07B576F77 FOREIGN KEY (requirement_id) REFERENCES queue (id)');
        $this->addSql('ALTER TABLE queue ADD commit_id INT NOT NULL, DROP branch, DROP commit');
        $this->addSql('ALTER TABLE queue ADD CONSTRAINT FK_7FFD7F633D5814AC FOREIGN KEY (commit_id) REFERENCES commit (id)');
        $this->addSql('CREATE INDEX IDX_7FFD7F633D5814AC ON queue (commit_id)');
    }

    /**
     * @param Schema $schema
     */
    public function down(Schema $schema)
    {
        // this down() migration is auto-generated, please modify it to your needs
        $this->abortIf($this->connection->getDatabasePlatform()->getName() !== 'mysql', 'Migration can only be executed safely on \'mysql\'.');

        $this->addSql('ALTER TABLE queue DROP FOREIGN KEY FK_7FFD7F633D5814AC');
        $this->addSql('DROP TABLE commit');
        $this->addSql('DROP TABLE queue_dependency');
        $this->addSql('DROP INDEX IDX_7FFD7F633D5814AC ON queue');
        $this->addSql('ALTER TABLE queue ADD branch VARCHAR(100) NOT NULL COLLATE utf8mb4_unicode_ci, ADD commit VARCHAR(64) NOT NULL COLLATE utf8mb4_unicode_ci, DROP commit_id');
    }
}
