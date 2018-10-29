<?php

namespace App\Repository;

use App\Entity\QueueDependency;
use Doctrine\Bundle\DoctrineBundle\Repository\ServiceEntityRepository;
use Symfony\Bridge\Doctrine\RegistryInterface;

/**
 * @method QueueDependency|null find($id, $lockMode = null, $lockVersion = null)
 * @method QueueDependency|null findOneBy(array $criteria, array $orderBy = null)
 * @method QueueDependency[]    findAll()
 * @method QueueDependency[]    findBy(array $criteria, array $orderBy = null, $limit = null, $offset = null)
 */
class QueueDependencyRepository extends ServiceEntityRepository
{
    public function __construct(RegistryInterface $registry)
    {
        parent::__construct($registry, QueueDependency::class);
    }

//    /**
//     * @return QueueDependency[] Returns an array of QueueDependency objects
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
    public function findOneBySomeField($value): ?QueueDependency
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
