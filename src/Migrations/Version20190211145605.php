<?php

namespace DoctrineMigrations;

use Doctrine\DBAL\Migrations\AbstractMigration;
use Doctrine\DBAL\Schema\Schema;

/**
 * Auto-generated Migration: Please modify to your needs!
 */
class Version20190211145605 extends AbstractMigration
{
    /**
     * @param Schema $schema
     */
    public function up(Schema $schema)
    {
        // this up() migration is auto-generated, please modify it to your needs
        $this->abortIf($this->connection->getDatabasePlatform()->getName() !== 'mysql', 'Migration can only be executed safely on \'mysql\'.');

        $this->addSql('CREATE TABLE package (id INT AUTO_INCREMENT NOT NULL, aport VARCHAR(100) NOT NULL, arch VARCHAR(10) NOT NULL, component VARCHAR(30) NOT NULL, PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE package_dependency (id INT AUTO_INCREMENT NOT NULL, package_id INT NOT NULL, requirement_id INT NOT NULL, INDEX IDX_2344A0F0F44CABFF (package_id), INDEX IDX_2344A0F07B576F77 (requirement_id), PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE = InnoDB');
        $this->addSql('ALTER TABLE package_dependency ADD CONSTRAINT FK_2344A0F0F44CABFF FOREIGN KEY (package_id) REFERENCES package (id)');
        $this->addSql('ALTER TABLE package_dependency ADD CONSTRAINT FK_2344A0F07B576F77 FOREIGN KEY (requirement_id) REFERENCES package (id)');
        $this->addSql('DROP TABLE queue_dependency');
        $this->addSql('ALTER TABLE queue ADD package_id INT NOT NULL, DROP aport, DROP arch, DROP component');
        $this->addSql('ALTER TABLE queue ADD CONSTRAINT FK_7FFD7F63F44CABFF FOREIGN KEY (package_id) REFERENCES package (id)');
        $this->addSql('CREATE INDEX IDX_7FFD7F63F44CABFF ON queue (package_id)');
    }

    /**
     * @param Schema $schema
     */
    public function down(Schema $schema)
    {
        // this down() migration is auto-generated, please modify it to your needs
        $this->abortIf($this->connection->getDatabasePlatform()->getName() !== 'mysql', 'Migration can only be executed safely on \'mysql\'.');

        $this->addSql('ALTER TABLE queue DROP FOREIGN KEY FK_7FFD7F63F44CABFF');
        $this->addSql('ALTER TABLE package_dependency DROP FOREIGN KEY FK_2344A0F0F44CABFF');
        $this->addSql('ALTER TABLE package_dependency DROP FOREIGN KEY FK_2344A0F07B576F77');
        $this->addSql('CREATE TABLE queue_dependency (id INT AUTO_INCREMENT NOT NULL, requirement_id INT NOT NULL, queue_item_id INT NOT NULL, INDEX IDX_90AE2CA0F0EDC960 (queue_item_id), INDEX IDX_90AE2CA07B576F77 (requirement_id), PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci ENGINE = InnoDB');
        $this->addSql('ALTER TABLE queue_dependency ADD CONSTRAINT FK_90AE2CA07B576F77 FOREIGN KEY (requirement_id) REFERENCES queue (id)');
        $this->addSql('ALTER TABLE queue_dependency ADD CONSTRAINT FK_90AE2CA0F0EDC960 FOREIGN KEY (queue_item_id) REFERENCES queue (id)');
        $this->addSql('DROP TABLE package');
        $this->addSql('DROP TABLE package_dependency');
        $this->addSql('DROP INDEX IDX_7FFD7F63F44CABFF ON queue');
        $this->addSql('ALTER TABLE queue ADD aport VARCHAR(100) NOT NULL COLLATE utf8mb4_unicode_ci, ADD arch VARCHAR(10) NOT NULL COLLATE utf8mb4_unicode_ci, ADD component VARCHAR(30) NOT NULL COLLATE utf8mb4_unicode_ci, DROP package_id');
    }
}
