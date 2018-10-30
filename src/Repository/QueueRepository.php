<?php

namespace App\Repository;

use App\Entity\Queue;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Symfony\Bridge\Doctrine\RegistryInterface;

/**
 * @method Queue|null find($id, $lockMode = null, $lockVersion = null)
 * @method Queue|null findOneBy(array $criteria, array $orderBy = null)
 * @method Queue[]    findAll()
 * @method Queue[]    findBy(array $criteria, array $orderBy = null, $limit = null, $offset = null)
 */
class QueueRepository extends ServiceEntityRepository
{
    public function __construct(RegistryInterface $registry)
    {
        parent::__construct($registry, Queue::class);
    }

    public function getStartable()
    {
        $conn = $this->getEntityManager()->getConnection();
        $stmt = $conn->prepare('
            SELECT queue.id, GROUP_CONCAT(DISTINCT depend.status) as dependencies
            FROM queue
                        LEFT JOIN queue_depends ON queue_depends.queue_id = queue.id
                        LEFT JOIN queue AS depend ON depend.id = queue_depends.requires_id
            WHERE queue.status = "WAITING"
            GROUP BY queue.aport
        ');

        $stmt->execute();

        $result = [];
        foreach ($stmt->fetchAll() as $row) {
            if ($row['dependencies'] === null || $row['dependencies'] == 'DONE') {
                $result[] = $row['id'];
            }
        }
        return $this->findBy(['id' => $result]);
    }

//    /**
//     * @return Queue[] Returns an array of Queue objects
//     */
    /*
    public function findByExampleField($value)
    {
        return $this->createQueryBuilder('q')
            ->andWhere('q.exampleField = :val')
            ->setParameter('val', $value)
            ->orderBy('q.id', 'ASC')
            ->setMaxResults(10)
            ->getQuery()
            ->getResult()
        ;
    }
    */

    /*
    public function findOneBySomeField($value): ?Queue
    {
        return $this->createQueryBuilder('q')
            ->andWhere('q.exampleField = :val')
            ->setParameter('val', $value)
            ->getQuery()
            ->getOneOrNullResult()
        ;
    }
    */
}
