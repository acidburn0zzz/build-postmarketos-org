<?php

namespace DoctrineMigrations;

use Doctrine\DBAL\Migrations\AbstractMigration;
use Doctrine\DBAL\Schema\Schema;

/**
 * Auto-generated Migration: Please modify to your needs!
 */
class Version20190212161116 extends AbstractMigration
{
    /**
     * @param Schema $schema
     */
    public function up(Schema $schema)
    {
        // this up() migration is auto-generated, please modify it to your needs
        $this->abortIf($this->connection->getDatabasePlatform()->getName() !== 'mysql', 'Migration can only be executed safely on \'mysql\'.');

        $this->addSql('CREATE TABLE package (id INT AUTO_INCREMENT NOT NULL, aport VARCHAR(100) NOT NULL, arch VARCHAR(10) NOT NULL, component VARCHAR(30) NOT NULL, time_spent BIGINT DEFAULT NULL, times_built INT DEFAULT NULL, PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE commit (id INT AUTO_INCREMENT NOT NULL, ref VARCHAR(64) NOT NULL, branch VARCHAR(100) NOT NULL, message LONGTEXT NOT NULL, status VARCHAR(20) NOT NULL, PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE log (id INT AUTO_INCREMENT NOT NULL, datetime DATETIME NOT NULL, action VARCHAR(100) NOT NULL, details LONGTEXT DEFAULT NULL, PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE queue (id INT AUTO_INCREMENT NOT NULL, package_id INT NOT NULL, commit_id INT NOT NULL, pkgver VARCHAR(100) NOT NULL, pkgrel INT NOT NULL, srht_id INT DEFAULT NULL, status VARCHAR(10) NOT NULL, time_spent INT DEFAULT NULL, time_started DATETIME DEFAULT NULL, INDEX IDX_7FFD7F63F44CABFF (package_id), INDEX IDX_7FFD7F633D5814AC (commit_id), PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE = InnoDB');
        $this->addSql('CREATE TABLE package_dependency (id INT AUTO_INCREMENT NOT NULL, package_id INT NOT NULL, requirement_id INT NOT NULL, INDEX IDX_2344A0F0F44CABFF (package_id), INDEX IDX_2344A0F07B576F77 (requirement_id), PRIMARY KEY(id)) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci ENGINE = InnoDB');
        $this->addSql('ALTER TABLE queue ADD CONSTRAINT FK_7FFD7F63F44CABFF FOREIGN KEY (package_id) REFERENCES package (id)');
        $this->addSql('ALTER TABLE queue ADD CONSTRAINT FK_7FFD7F633D5814AC FOREIGN KEY (commit_id) REFERENCES commit (id)');
        $this->addSql('ALTER TABLE package_dependency ADD CONSTRAINT FK_2344A0F0F44CABFF FOREIGN KEY (package_id) REFERENCES package (id)');
        $this->addSql('ALTER TABLE package_dependency ADD CONSTRAINT FK_2344A0F07B576F77 FOREIGN KEY (requirement_id) REFERENCES package (id)');
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
        $this->addSql('ALTER TABLE queue DROP FOREIGN KEY FK_7FFD7F633D5814AC');
        $this->addSql('DROP TABLE package');
        $this->addSql('DROP TABLE commit');
        $this->addSql('DROP TABLE log');
        $this->addSql('DROP TABLE queue');
        $this->addSql('DROP TABLE package_dependency');
    }
}
